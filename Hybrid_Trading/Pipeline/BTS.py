from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Hybrid_Trading.Backtester.Day_Trading_Backtester import DayTradingBacktester
from tqdm import tqdm
import time

class BacktestingStage:
    def __init__(self, user_input: Any, max_workers: int = 20):
        self.user_input = user_input
        self.logger = LoggingMaster("BacktestingStage").get_logger()
        self.max_workers = max_workers

        # Extract user input parameters that are required for the backtesting
        self.start_date = user_input.get('start_date')
        self.end_date = user_input.get('end_date')
        self.interval = user_input.get('interval')
        self.period = user_input.get('period')

    def backtest_ticker(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the backtest for a single ticker.

        :param ticker: The ticker symbol.
        :param data: The data dictionary for the ticker.
        :return: The updated data dictionary with backtest results included.
        """
        self.logger.info(f"Starting backtesting for {ticker}...")

        try:
            # Access the required data for the ticker
            historical_data = data.get('historical_data')
            prophet_forecast = data.get('prophet_forecast')

            # Check for essential data
            if historical_data is None or historical_data.empty or prophet_forecast is None or prophet_forecast.empty:
                self.logger.warning(f"Missing essential data for {ticker}. Skipping backtesting.")
                data.update({'status': 'failed', 'reason': 'MissingData'})
                return data

            # Combine the essential data for backtesting
            combined_data = {
                'ticker': ticker,
                'historical_data': historical_data,
                'prophet_forecast': prophet_forecast,
                'real_time_data': data.get('real_time_data', {}),
                'technical_indicators': data.get('technical_indicators', {}),
                'start_date': self.start_date,
                'end_date': self.end_date,
                'interval': self.interval,
                'period': self.period
            }

            # Define file path for saving the backtest results
            file_path = f"/Volumes/TDBTR/{ticker}_backtest_results.xlsx"

            # Initialize the DayTradingBacktester with user_input and file_path
            backtester = DayTradingBacktester(user_input=self.user_input, filepath=file_path)

            # Run the backtest
            backtest_result = backtester.run(combined_data)

            if backtest_result.get("status") == "success":
                self.logger.info(f"Backtesting completed successfully for {ticker}")
            else:
                self.logger.warning(f"Backtesting failed for {ticker}")

            # Merge the backtest results into the data object
            data.update({'backtest_result': backtest_result})

        except KeyError as e:
            self.logger.error(f"KeyError during backtesting for {ticker}: {e}")
            data.update({'status': 'failed', 'reason': f'Missing key: {str(e)}'})
        except Exception as e:
            self.logger.error(f"Error during backtesting for {ticker}: {e}")
            data.update({'status': 'failed', 'reason': str(e)})

        return data

    def estimate_time_remaining(self, completed_tasks: int, total_tasks: int, start_time: float) -> float:
        """
        Estimate the remaining time for the current process.

        :param completed_tasks: Number of completed tasks so far.
        :param total_tasks: Total number of tasks.
        :param start_time: Time when the process started.
        :return: Estimated remaining time in seconds.
        """
        elapsed_time = time.time() - start_time
        average_time_per_task = elapsed_time / completed_tasks if completed_tasks > 0 else 0
        remaining_tasks = total_tasks - completed_tasks
        return average_time_per_task * remaining_tasks

    def run(self, fetched_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Run the backtesting stage for each ticker in the fetched_data dictionary using parallel processing.

        :param fetched_data: A dictionary where the key is the ticker symbol and the value is another dictionary containing the data for that ticker.
        :return: The updated fetched_data dictionary with backtest results included.
        """
        self.logger.info("Starting backtesting run...")
        print("Starting backtesting run...")

        results = {}
        start_time = time.time()

        # Convert fetched_data to a dictionary if it isn't already one
        if isinstance(fetched_data, str):
            fetched_data = {fetched_data: {}}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {executor.submit(self.backtest_ticker, ticker, data): ticker for ticker, data in fetched_data.items()}

            for i, future in enumerate(tqdm(as_completed(future_to_ticker), total=len(future_to_ticker), desc="Backtesting Progress")):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results[ticker] = result
                except Exception as e:
                    self.logger.error(f"Error processing ticker {ticker}: {e}")
                    fetched_data[ticker].update({'status': 'failed', 'reason': str(e)})
                    results[ticker] = fetched_data[ticker]

                # Estimate and log remaining time
                estimated_time_remaining = self.estimate_time_remaining(i + 1, len(future_to_ticker), start_time)
                self.logger.info(f"Estimated time remaining: {estimated_time_remaining:.2f} seconds")

        self.logger.info("Backtesting run completed.")
        print("Backtesting run completed.")
        return results