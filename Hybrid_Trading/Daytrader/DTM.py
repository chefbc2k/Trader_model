import logging
import asyncio
from django.utils.timezone import now
from Hybrid_Trading.Pipeline.FDS import FetchDataStage
from Hybrid_Trading.Pipeline.GSS import GenerateSignalsStage
from Hybrid_Trading.Pipeline.EXECTS import ExecuteTradesStage
from Hybrid_Trading.Pipeline.TPS import TrackPerformanceStage
from Config.trading_constants import TCS
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
import aiohttp
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid  # For generating unique task IDs

class DTPipelineOrchestrator:
    def __init__(self, tickers, interval, start_date, end_date, period, fillna_method, sentiment_type):
        """
        Initialize the pipeline orchestrator using form data.
        """
        self.tickers = tickers
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.fillna_method = fillna_method
        self.sentiment_type = sentiment_type
        self.task_id = str(uuid.uuid4())  # Generate unique task ID using uuid
        self.logger = LoggingMaster("TradingPipelineOrchestrator").get_logger()

        # Initializing each pipeline stage with relevant parameters
        self.fetch_stage = FetchDataStage(tickers, interval, start_date, end_date, period, fillna_method)
        self.generate_signals_stage = GenerateSignalsStage(tickers, start_date, end_date, fillna_method, sentiment_type)
        self.execute_trades_stage = ExecuteTradesStage(tickers)
        self.track_performance_stage = TrackPerformanceStage(tickers)  # This should be the final stage
        self.tcs = TCS()
        self.BLACKLIST = self.tcs.BLACKLIST

        # Shared state for progress tracking
        self.total_steps = len(self.tickers) * 4  # Assuming 4 stages per ticker
        self.completed_steps = 0
        self.lock = asyncio.Lock()  # To ensure thread-safe updates

        # Initialize channel layer for WebSocket communication
        self.channel_layer = get_channel_layer()
        self.group_name = f'progress_{self.task_id}'  # Group name for sending WebSocket updates

    async def run_day_trading_pipeline(self):
        """
        Run the entire day trading pipeline asynchronously.
        """
        self.logger.info("Starting the day trading pipeline.")

        # Send initial progress update via WebSocket
        await self.send_progress(status='running', progress=0, message='Pipeline started.')

        # Check for blacklisted tickers
        if any(blacklisted in self.tickers for blacklisted in self.BLACKLIST):
            self.logger.warning("Ticker list contains blacklisted items and will not be processed.")
            await self.send_progress(status='error', progress=100, message='Ticker list contains blacklisted items.')
            return

        try:
            # Create a single session for all HTTP requests
            async with aiohttp.ClientSession() as session:
                tasks = [self.process_ticker(ticker, session) for ticker in self.tickers]
                await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error processing tickers: {e}")
            await self.send_progress(status='error', progress=100, message=f"An error occurred: {str(e)}")
            return

        # Finalize progress
        await self.send_progress(status='completed', progress=100, message='Pipeline completed successfully.')
        self.logger.info("Day trading pipeline completed successfully.")

    async def process_ticker(self, ticker, session):
        """
        Process each ticker asynchronously by running through all pipeline stages.
        """
        self.logger.info(f"Starting pipeline for ticker: {ticker}")

        # 1. Fetch Data Stage
        try:
            fetch_success = await self.fetch_stage.fetch_data_for_ticker(ticker, session)
            self.logger.debug(f"Fetch Data Stage outcome for {ticker}: {fetch_success}")
            if not fetch_success:
                self.logger.error(f"Fetch Data Stage failed for {ticker}. Skipping to next ticker.")
                await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Fetch Data Stage failed for {ticker}.")
                return
        except Exception as e:
            self.logger.error(f"Error in Fetch Data Stage for {ticker}: {e}")
            await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Error in Fetch Data Stage for {ticker}: {str(e)}")
            return

        # Update progress after Fetch Data Stage
        await self.increment_progress(message=f"Fetch Data Stage completed for {ticker}.")

        # 2. Generate Signals Stage
        try:
            signals_success = await self.generate_signals_stage.run([ticker])
            self.logger.debug(f"Generate Signals Stage outcome for {ticker}: {signals_success}")
            if not signals_success:
                self.logger.error(f"Generate Signals Stage failed for {ticker}. Skipping to next ticker.")
                await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Generate Signals Stage failed for {ticker}.")
                return
        except Exception as e:
            self.logger.error(f"Error in Generate Signals Stage for {ticker}: {e}")
            await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Error in Generate Signals Stage for {ticker}: {str(e)}")
            return

        # Update progress after Generate Signals Stage
        await self.increment_progress(message=f"Generate Signals Stage completed for {ticker}.")

        # 3. Execute Trades Stage
        try:
            trades_success = await self.execute_trades_stage.run([ticker])
            self.logger.debug(f"Execute Trades Stage outcome for {ticker}: {trades_success}")
            if not trades_success:
                self.logger.error(f"Execute Trades Stage failed for {ticker}. Proceeding to performance tracking.")
                await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Execute Trades Stage failed for {ticker}.")
        except Exception as e:
            self.logger.error(f"Error in Execute Trades Stage for {ticker}: {e}")
            await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Error in Execute Trades Stage for {ticker}: {str(e)}")

        # Update progress after Execute Trades Stage
        await self.increment_progress(message=f"Execute Trades Stage completed for {ticker}.")

        # 4. Track Performance Stage (final stage)
        try:
            performance_success = await self.track_performance_stage.run([ticker])
            self.logger.debug(f"Track Performance Stage outcome for {ticker}: {performance_success}")
        except Exception as e:
            self.logger.error(f"Error in Track Performance Stage for {ticker}: {e}")
            await self.send_progress(status='running', progress=self.calculate_progress(), message=f"Error in Track Performance Stage for {ticker}: {str(e)}")

        # Update progress after Track Performance Stage
        await self.increment_progress(message=f"Track Performance Stage completed for {ticker}.")

        self.logger.info(f"Ticker {ticker} processed through all stages.")

    async def send_progress(self, status, progress, message):
        """
        Send a progress update to the WebSocket group.
        """
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'progress_update',
                'status': status,
                'progress': progress,
                'message': message
            }
        )

    async def increment_progress(self, message):
        """
        Safely increment the completed steps and update the progress percentage.
        """
        async with self.lock:
            self.completed_steps += 1
            progress_percentage = int((self.completed_steps / self.total_steps) * 100)
            await self.send_progress(status='running', progress=progress_percentage, message=message)

    def calculate_progress(self):
        """
        Calculate the current progress percentage.
        """
        if self.total_steps == 0:
            return 100
        return int((self.completed_steps / self.total_steps) * 100)