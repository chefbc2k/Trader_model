from typing import Dict, List, Any
import pandas as pd
from tqdm.asyncio import tqdm_asyncio
from Hybrid_Trading.Forecaster.models import TimeSeriesForecasts
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Hybrid_Trading.Strategy.Strats.Dynamic_Strategy import DynamicStrategy
from Hybrid_Trading.Strategy.Strats.IBS import TradingStrategy
from Hybrid_Trading.Strategy.Strats.MRMS import MeanReversionMomentumStrategy
from Hybrid_Trading.Strategy.Strats.Prediction_Strategy import PredictionStrategy
from Hybrid_Trading.Strategy.Strats.VRS import VolatilityReversionStrategy
from Hybrid_Trading.Strategy.Strats.VS import ValueSeekerStrategy
from Config.trading_constants import TCS
from Hybrid_Trading.Data.models import RealTimePrice, HistoricalPrice, FinancialScores, TechnicalIndicators, TempFiles
from asgiref.sync import sync_to_async

class GenerateSignalsStage:
    def __init__(self, tickers: List[str], start_date: str, end_date: str, fillna_method: str, sentiment_type: str):
        """
        Initialize the GenerateSignalsStage class.

        Parameters:
        - tickers: List of stock tickers.
        - start_date: Start date for the data.
        - end_date: End date for the data.
        - fillna_method: Method to handle missing values.
        - sentiment_type: Type of sentiment analysis to be applied.
        """
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.fillna_method = fillna_method
        self.sentiment_type = sentiment_type

        self.logger = LoggingMaster('GenerateSignalsStage').get_logger()
        self.constants = TCS()  # Initialize the TCS class for constants

        # List of strategies to apply with indication of required format
        self.strategies = {
            "dynamic": DynamicStrategy,
            "prediction": PredictionStrategy,
            "mean_reversion_momentum": MeanReversionMomentumStrategy,
            "volatility_reversion": VolatilityReversionStrategy,
            "trading": TradingStrategy,
            "value_seeker": ValueSeekerStrategy
        }

        # Strategies that need Pandas DataFrames
        self.pandas_strategies = ["dynamic", "mean_reversion_momentum", "instant_backtesting"]

        # Strategies that work with JSON format
        self.json_strategies = ["value_seeker", "volatility_reversion", "prediction"]

    async def retrieve_ticker_data(self, ticker):
        """Retrieve the necessary data for a ticker using Django ORM."""
        try:
            # Retrieve real-time price, historical price, financial scores, technical indicators, and forecast data
            prophet_forecast_data = await sync_to_async(TimeSeriesForecasts.objects.filter(ticker=ticker).values)()
            real_time_data = await sync_to_async(RealTimePrice.objects.filter(ticker=ticker).values)()
            technical_indicators = await sync_to_async(TechnicalIndicators.objects.filter(ticker=ticker).values)()
            financial_scores = await sync_to_async(FinancialScores.objects.filter(ticker=ticker).values)()
            historical_price = await sync_to_async(HistoricalPrice.objects.filter(ticker=ticker).values)()

            return {
                "prophet_forecast": list(prophet_forecast_data),
                "real_time_data": list(real_time_data),
                "technical_indicators": list(technical_indicators),
                "financial_scores": list(financial_scores),
                "historical_price": list(historical_price)
            }
        except Exception as e:
            self.logger.error(f"Error retrieving data for ticker {ticker}: {e}")
            return None

    async def process_ticker(self, ticker: str) -> Dict[str, Any]:
        self.logger.info(f"Generating trading signals for {ticker}...")

        try:
            # Retrieve the necessary data using Django's ORM
            ticker_data = await self.retrieve_ticker_data(ticker)
            
            if ticker_data is None:
                self.logger.error(f"No data found for ticker {ticker}")
                return None

            # Convert to Pandas DataFrame for strategies that require DataFrames
            prophet_forecast_df = pd.DataFrame(ticker_data.get("prophet_forecast", []))
            real_time_data_df = pd.DataFrame(ticker_data.get("real_time_data", []))
            technical_indicators_df = pd.DataFrame(ticker_data.get("technical_indicators", []))
            financial_scores_df = pd.DataFrame(ticker_data.get("financial_scores", []))
            historical_price_df = pd.DataFrame(ticker_data.get("historical_price", []))

            # Prepare results dictionary
            strategy_results = {}

            # Process strategies requiring Pandas DataFrames
            for strategy_key in self.pandas_strategies:
                strategy_cls = self.strategies[strategy_key]
                strategy_instance = strategy_cls(
                    ticker=ticker,
                    prophet_forecast=prophet_forecast_df,
                    real_time_data=real_time_data_df,
                    technical_indicators=technical_indicators_df,
                    sentiment_score=ticker_data.get('sentiment_score', 0.0),
                    constants=self.constants,
                    temp_files=TempFiles(),  # Replacing old temp file logic
                    logger=self.logger
                )
                strategy_name = strategy_cls.__name__
                strategy_results[f"{strategy_name.lower()}_signals"] = await strategy_instance.apply_strategy()

            # Process strategies requiring JSON format
            for strategy_key in self.json_strategies:
                strategy_cls = self.strategies[strategy_key]
                strategy_instance = strategy_cls(
                    ticker=ticker,
                    prophet_forecast=ticker_data.get("prophet_forecast", []),
                    real_time_data=ticker_data.get("real_time_data", []),
                    technical_indicators=ticker_data.get("technical_indicators", []),
                    sentiment_score=ticker_data.get('sentiment_score', 0.0),
                    constants=self.constants,
                    temp_files=TempFiles(),  # Replacing old temp file logic
                    logger=self.logger
                )
                strategy_name = strategy_cls.__name__
                strategy_results[f"{strategy_name.lower()}_signals"] = await strategy_instance.apply_strategy()

            self.logger.info(f"Strategy results for {ticker}: {strategy_results}")

            # Aggregate signals from all strategies
            signals = {**strategy_results}

            # Store the generated signals in the database model (TempFiles or custom model for signals)
            await sync_to_async(TempFiles.objects.update_or_create)(ticker=ticker, defaults={"signals": signals})

            return signals
        except Exception as e:
            self.logger.error(f"Error generating signals for {ticker}: {e}")
            return None

    async def run(self, tickers: List[str]):
        total_tickers = len(tickers)
        tasks = [self.process_ticker(ticker) for ticker in tickers]

        # Integrate TQDM for progress tracking with asyncio
        for task in tqdm_asyncio.as_completed(tasks, total=total_tickers, desc="Generating Signals", unit="ticker"):
            await task