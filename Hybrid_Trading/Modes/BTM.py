import time
import pandas as pd
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from Hybrid_Trading.Pipeline.FDS import FetchDataStage  # Fetch Data Stage
from Hybrid_Trading.Pipeline.BTS import BacktestingStage  # Backtesting Stage
from Hybrid_Trading.Pipeline.TPS import TrackPerformanceStage  # Tracking Performance Stage
from Config.trading_constants import TCS
from Config.utils import TempFiles  # Assuming TempFiles is in Utilities directory
from Config.utils import TradingDataWorkbook  # Assuming TradingDataWorkbook is in Utilities directory
from asgiref.sync import sync_to_async

class BacktesterPipeline:
    def __init__(self, form_data):
        """
        Initialize the BacktesterPipeline with the form data from the user.
        """
        self.form_data = form_data
        self.tickers = form_data.get('tickers')
        self.constants = TCS()  # Initialize constants
        self.logger = logging.getLogger("BacktesterPipeline")

    async def process_ticker(self, ticker):
        """
        Process a single ticker through the backtesting pipeline.
        """
        try:
            self.logger.info(f"Processing ticker: {ticker}")

            # Initialize TempFiles and TradingDataWorkbook for each ticker
            temp_files = TempFiles()
            trading_workbook = TradingDataWorkbook(ticker)

            # Fetch Data Stage
            fetch_data_stage = FetchDataStage(self.form_data)
            historical_data = await sync_to_async(fetch_data_stage.fetch_data_for_ticker)(ticker)
            if historical_data.empty:
                self.logger.warning(f"No historical data available for {ticker}")
                return None

            # Save raw data to workbook
            await sync_to_async(trading_workbook.save_to_sheet)(historical_data, "Raw Data")

            # Introduce a buffer to ensure data is fully processed
            time.sleep(2 * 60)  # 2-minute buffer, adjust based on actual needs

            # Backtesting Stage
            backtesting_stage = BacktestingStage(self.form_data)
            backtest_results = await sync_to_async(backtesting_stage.run_backtesting)(historical_data, ticker)

            # Save backtesting results to workbook
            await sync_to_async(trading_workbook.save_to_sheet)(backtest_results, "Backtesting Results")

            self.logger.info(f"Backtesting results for {ticker} exported.")

            # Tracking Performance Stage
            tracking_performance_stage = TrackPerformanceStage(self.form_data)
            performance_metrics = await sync_to_async(tracking_performance_stage.track_performance)(backtest_results, historical_data)

            # Save performance metrics to workbook
            await sync_to_async(trading_workbook.save_to_sheet)(performance_metrics, "Performance Metrics")

            # Summarize results and save to workbook
            summary_data = pd.DataFrame({
                'Summary': ['Backtesting Results', 'Performance Metrics'],
                'Data': [len(backtest_results), len(performance_metrics)]
            })
            await sync_to_async(trading_workbook.save_to_sheet)(summary_data, "Summary")

            self.logger.info(f"Backtesting process completed for {ticker}")

            # Clean up temporary files
            await sync_to_async(temp_files.cleanup_temp_files)()

            return ticker

        except Exception as e:
            self.logger.error(f"Error backtesting {ticker}: {e}")
            return None

    async def run_pipeline(self):
        """
        Run the backtesting pipeline on all tickers.
        """
        self.logger.info("Starting the backtesting pipeline.")

        # Use ThreadPoolExecutor to process tickers in parallel without blocking the web request
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = {executor.submit(sync_to_async(self.process_ticker), ticker): ticker for ticker in self.tickers}
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    result = await future.result()
                    if result:
                        self.logger.info(f"Completed backtesting for {ticker}")
                        # Store progress in cache or database for frontend progress tracking
                except Exception as e:
                    self.logger.error(f"Exception occurred for {ticker}: {e}")

        self.logger.info("Backtesting process completed for all tickers.")