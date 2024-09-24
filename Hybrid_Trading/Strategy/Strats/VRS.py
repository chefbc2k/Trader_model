import pandas as pd
import datetime
from typing import Dict, Any, List
from tqdm.asyncio import tqdm_asyncio
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.utils import TradingDataWorkbook, TempFiles

class VolatilityReversionStrategy:
    def __init__(
        self, 
        ticker: str, 
        real_time_data: pd.DataFrame, 
        technical_indicators: pd.DataFrame, 
        sentiment_score: float, 
        constants: Any, 
        user_input: Any, 
        temp_files: TempFiles
    ):
        self.ticker = ticker
        self.start_date = user_input.get('start_date')
        self.end_date = user_input.get('end_date')
        self.real_time_data = real_time_data
        self.technical_indicators = technical_indicators
        self.sentiment_score = sentiment_score
        self.constants = constants
        self.user_input = user_input
        self.logger = LoggingMaster("VolatilityReversionStrategy").get_logger()
        self.trading_workbook = TradingDataWorkbook(ticker=self.ticker)
        self.temp_files = temp_files

    def apply_strategy(self) -> Dict[str, Any]:
        current_date = datetime.date.today()
        current_price = self.real_time_data['lastSalePrice']

        # Retrieve Bollinger Bands and RSI from technical indicators
        upper_band = self.technical_indicators.get('bollinger_upper', None)
        lower_band = self.technical_indicators.get('bollinger_lower', None)
        rsi = self.technical_indicators.get('rsi', None)

        if upper_band is None or lower_band is None or rsi is None:
            self.logger.error(f"Missing Bollinger Bands or RSI for {self.ticker}.")
            return {}

        # Strategy logic and signal creation
        signal = {
            'ticker': self.ticker,
            'date': str(current_date),
            'action': 'Hold',
            'reason': 'No strong buy or sell signal',
            'current_price': current_price,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'rsi': rsi,
        }

        if current_price >= upper_band and rsi > 70:
            signal['action'] = 'Sell'
            signal['reason'] = 'Price is at or above the upper Bollinger Band and RSI indicates overbought conditions.'
        elif current_price <= lower_band and rsi < 30:
            signal['action'] = 'Buy'
            signal['reason'] = 'Price is at or below the lower Bollinger Band and RSI indicates oversold conditions.'

        self.logger.info(f"Strategy decision for {self.ticker}: {signal}")
        print(f"Strategy decision for {self.ticker}: {signal}")

        # Save decision to the trading workbook
        self.trading_workbook.save_to_sheet({self.ticker: signal}, "Strategy Decisions")
        return signal

    async def run(self) -> Dict[str, Any]:
        self.logger.info(f"Running volatility-based reversion strategy for {self.ticker}...")
        print(f"Running volatility-based reversion strategy for {self.ticker}...")

        decision = self.apply_strategy()

        # Save the decision
        await self.trading_workbook.save_to_sheet({self.ticker: decision}, "Strategy Decisions")

        self.logger.info(f"Volatility-based reversion strategy for {self.ticker} completed.")
        print(f"Volatility-based reversion strategy for {self.ticker} completed.")

        return decision

async def run_volatility_reversion_strategy(
    tickers: List[str], 
    real_time_data: Dict[str, pd.DataFrame], 
    technical_indicators: Dict[str, pd.DataFrame], 
    sentiment_scores: Dict[str, float], 
    constants: Any, 
    user_input: Any, 
    temp_files: TempFiles
) -> Dict[str, Dict[str, Any]]:
    results = {}

    tasks = [
        VolatilityReversionStrategy(
            ticker=ticker,
            real_time_data=real_time_data[ticker],
            technical_indicators=technical_indicators[ticker],
            sentiment_score=sentiment_scores.get(ticker, 0),
            constants=constants,
            user_input=user_input,
            temp_files=temp_files
        ).run() for ticker in tickers
    ]

    # Use tqdm_asyncio to track progress
    async for task in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Processing Tickers", unit="ticker"):
        result = await task
        ticker = result.get('ticker')
        results[ticker] = result

    return results