from typing import List, Dict, Any
import pandas as pd
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.utils import TradingDataWorkbook
from Hybrid_Trading.Trading.Alpaca.PM import PerformanceMetrics
from tqdm.asyncio import tqdm_asyncio

class TrackPerformanceStage:
    def __init__(self, user_input):
        self.logger = LoggingMaster("TrackPerformanceStage").get_logger()
        self.user_input = user_input  # Store user input for flexibility

    async def run(self, tickers: List[str], user_input: Dict[str, Any], data: Dict[str, Any]) -> None:
        self.logger.info("Tracking performance metrics...")

        if not tickers or not isinstance(tickers, list):
            self.logger.error("Invalid tickers list passed for performance tracking.")
            return

        try:
            all_metrics = {}

            tasks = []

            # Process tickers asynchronously and track progress using tqdm_asyncio
            for ticker in tickers:
                task = self.process_ticker(ticker, data)
                tasks.append(task)

            async for task in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Tracking Performance", unit="ticker"):
                await task

            # After all tasks complete, save metrics to the workbook in one go if needed
            if all_metrics:
                combined_metrics_df = pd.concat(all_metrics.values(), ignore_index=True)
                await TradingDataWorkbook.instance().save_to_sheet(combined_metrics_df, "All Performance Metrics")

            self.logger.info("Performance metrics tracked and saved to the workbook.")
        except Exception as e:
            self.logger.error(f"Error tracking performance metrics: {e}")

    async def process_ticker(self, ticker: str, data: Dict[str, Any]) -> None:
        """Process each ticker for performance metrics."""
        self.logger.info(f"Processing performance metrics for {ticker}...")

        # Retrieve trade results and signals from passed data (instead of CDS)
        trade_results = data.get(ticker, {}).get('trade_results')
        signals = data.get(ticker, {}).get('signals')

        if not trade_results or not signals:
            self.logger.warning(f"Missing trade results or signals for {ticker}. Skipping...")
            return

        # Extract necessary data for performance tracking
        sentiment_score = signals.get('sentiment_score', 0)
        weighted_sentiment = signals.get('weighted_sentiment', 0)
        analyst_score = signals.get('analyst_signal', 0)
        dynamic_decision = signals.get('dynamic_strategy', {}).get('action', 'Hold')
        prediction_decision = signals.get('prediction_strategy', {}).get('action', 'Hold')

        # Prepare the data for performance metrics calculation
        metrics_input = {
            'trade_results': trade_results,
            'dynamic_decision': dynamic_decision,
            'prediction_decision': prediction_decision,
            'sentiment_score': sentiment_score,
            'weighted_sentiment': weighted_sentiment,
            'analyst_score': analyst_score
        }

        # Calculate performance metrics
        metrics = PerformanceMetrics.calculate_metrics(pd.DataFrame([metrics_input]))

        # Store individual ticker metrics
        await TradingDataWorkbook.instance().save_to_sheet({ticker: metrics}, "Performance Metrics")

        self.logger.info(f"Performance metrics for {ticker} processed and saved.")