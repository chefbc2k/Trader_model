import pandas as pd
import datetime
from typing import Dict, Any, List
from tqdm.asyncio import tqdm_asyncio
from Config.trading_constants import TCS
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.utils import TradingDataWorkbook, TempFiles

class MeanReversionMomentumStrategy:
    def __init__(self, user_input: Any, logger=None):
        self.user_input = user_input
        self.constants = TCS()  # Initialize the TCS class for constants
        self.logger = logger or LoggingMaster("MeanReversionMomentumStrategy").get_logger()
        self.temp_files = TempFiles()

    def apply_strategy(self, ticker: str, real_time_data: pd.DataFrame, technical_indicators: pd.DataFrame) -> Dict[str, Any]:
        current_date = datetime.date.today()
        current_price = real_time_data['lastSalePrice']

        # Calculate the moving average
        moving_average = real_time_data['close'].rolling(window=20).mean().iloc[-1]

        # Determine the price deviation from the moving average
        price_deviation = current_price - moving_average

        # Calculate momentum as the rate of price change over the last 5 days
        momentum = (current_price - real_time_data['close'].iloc[-5]) / real_time_data['close'].iloc[-5]

        # Strategy logic and signal creation
        signal = {
            'ticker': ticker,
            'date': str(current_date),
            'action': 'Hold',
            'reason': 'No strong buy or sell signal',
            'current_price': current_price,
            'moving_average': moving_average,
            'momentum': momentum,
        }

        if price_deviation < -self.constants.MEAN_REVERSION_THRESHOLD and momentum > 0:
            signal['action'] = 'Buy'
            signal['reason'] = 'Price is below the moving average and momentum is positive.'
        elif price_deviation > self.constants.MEAN_REVERSION_THRESHOLD and momentum < 0:
            signal['action'] = 'Sell'
            signal['reason'] = 'Price is above the moving average and momentum is negative.'

        self.logger.info(f"Strategy decision for {ticker}: {signal}")
        print(f"Strategy decision for {ticker}: {signal}")

        # Save decision to the trading workbook
        trading_workbook = TradingDataWorkbook(ticker=ticker)
        trading_workbook.save_to_sheet({ticker: signal}, "Strategy Decisions")
        return signal

    async def run(self, tickers: List[str], fetched_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Run the strategy for each ticker.
        :param tickers: List of tickers.
        :param fetched_data: Data for each ticker containing real-time data and technical indicators.
        :return: Dictionary of results.
        """
        self.logger.info(f"Running mean reversion momentum strategy for tickers...")
        print(f"Running mean reversion momentum strategy for tickers...")

        results = {}
        tasks = [self.run_strategy_for_ticker(ticker, fetched_data[ticker]) for ticker in tickers]

        async for task in tqdm_asyncio.as_completed(tasks, total=len(tickers), desc="Processing Tickers", unit="ticker"):
            result = await task
            ticker = result.get('ticker')
            results[ticker] = result

        self.logger.info(f"Mean reversion momentum strategy completed for all tickers.")
        print(f"Mean reversion momentum strategy completed for all tickers.")
        return results

    async def run_strategy_for_ticker(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the strategy for a single ticker.
        :param ticker: Ticker symbol.
        :param data: Fetched data including real-time data and technical indicators.
        :return: Strategy result.
        """
        self.logger.info(f"Running strategy for ticker: {ticker}")

        # Extract necessary data from fetched_data (e.g., real-time data, technical indicators)
        real_time_data = pd.DataFrame(data.get('real_time_data', []))
        technical_indicators = pd.DataFrame(data.get('technical_indicators', []))

        if real_time_data.empty:
            self.logger.error(f"No real-time data available for {ticker}. Skipping strategy.")
            return None

        # Apply the strategy
        return self.apply_strategy(ticker, real_time_data, technical_indicators)