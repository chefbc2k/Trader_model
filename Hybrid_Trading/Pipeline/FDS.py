import asyncio
from datetime import datetime
from decimal import Decimal
from Hybrid_Trading.Symbols.models import Tickers
import aiohttp
import numpy as np
from Config.trading_constants import TCS  # Import the TCS class
from Hybrid_Trading.Analysis.models import NewsData
from Hybrid_Trading.Data.Data_Gathering.HD import HistoricalData
from Hybrid_Trading.Data.Data_Gathering.RT import RealTimeData
from Hybrid_Trading.Data.Data_Gathering.FS import FinancialScores
from Hybrid_Trading.Data.Data_Gathering.FR import FinancialRatios
from Hybrid_Trading.Analysis.News.news import NewsGetter
from Hybrid_Trading.Data.Data_Gathering.TI import TechnicalIndicatorFetcher
from Hybrid_Trading.Data.models import HistoricalPrice, RealTimePrice, TechnicalIndicators
from Hybrid_Trading.Forecaster.DTPF import DayTimeForecaster
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from asgiref.sync import sync_to_async

# Initialize the logger outside the class to avoid multiple initializations
logger = LoggingMaster("FetchDataStage").get_logger()

class FetchDataStage:
    def __init__(self, tickers, interval, start_date, end_date, period, fillna_method):
        """
        Initialize the data fetch stage with necessary parameters.
        """
        # Initialize TCS (trading constants)
        self.constants = TCS()

        # Parameters passed in from DTP pipeline
        self.tickers = tickers
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.fillna_method = fillna_method

        self.logger = logger
        self.rate_limit = 10
        self.retry_attempts = 3
        self.task_dict = {}
        self.lock_dict = {ticker: asyncio.Lock() for ticker in self.tickers}  # Initialize lock for each ticker

        # Initialize the necessary fetchers and classifiers with appropriate arguments
        # Pass tickers, start_date, end_date, interval, period where necessary
        self.technical_indicators_fetcher = TechnicalIndicatorFetcher(
            self.constants,
            tickers=self.tickers,
            start_date=self.start_date,
            end_date=self.end_date,
            period=self.period,
            interval=self.interval
        )
        self.historical_data_fetcher = HistoricalData(
            tickers=self.tickers,
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.interval,
            period=self.period
        )
        self.real_time_data_fetcher = RealTimeData(tickers=self.tickers)
        self.financial_scores = FinancialScores(tickers=self.tickers)
        self.financial_ratios = FinancialRatios(tickers=self.tickers)
        self.news_getter = NewsGetter(
            tickers=self.tickers,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self.forecaster = DayTimeForecaster(
            tickers=self.tickers,
            interval=self.interval,
            start_date=self.start_date,
            end_date=self.end_date,
            period=self.period
        )

    async def check_data_freshness(self, ticker_instance, data_type: str) -> bool:
        """Check if data is fresh based on the created_at timestamp."""
        latest_data = None

        if data_type == 'technical_indicators':
            latest_data = await sync_to_async(TechnicalIndicators.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()
        elif data_type == 'financial_ratios':
            latest_data = await sync_to_async(FinancialRatios.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()
        elif data_type == 'financial_scores':
            latest_data = await sync_to_async(FinancialScores.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()
        elif data_type == 'historical_price':
            latest_data = await sync_to_async(HistoricalPrice.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()
        elif data_type == 'real_time_price':
            latest_data = await sync_to_async(RealTimePrice.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()
        elif data_type == 'news':
            latest_data = await sync_to_async(NewsData.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()
        elif data_type == 'prophet_forecast':
            latest_data = await sync_to_async(DayTimeForecaster.objects.filter(ticker=ticker_instance).order_by('-created_at').first)()

        # Check if the latest data is fresh (created today)
        if latest_data and latest_data.created_at.date() == datetime.now().date():
            return True
        return False

    async def fetch_data_for_ticker(self, ticker: str, session: aiohttp.ClientSession) -> None:
        """Fetch all required data for a single ticker."""
        async with self.lock_dict[ticker]:
            try:
                # Fetch or create the Ticker instance
                ticker_instance, created = await sync_to_async(Tickers.objects.get_or_create)(ticker=ticker)
                self.logger.debug(f"Fetched Ticker instance: {ticker_instance}, Created: {created}")

                # Initialize the task dictionary if it doesn't exist
                if ticker not in self.task_dict:
                    self.task_dict[ticker] = {}

                # Initialize result_data and ensure it's always a dictionary
                self.task_dict[ticker]["result_data"] = self.task_dict[ticker].get("result_data", {})

                def is_numeric(value):
                    """Check if the value is numeric (int, float, Decimal)."""
                    return isinstance(value, (int, float, Decimal))

                def validate_numeric_fields(data):
                    """Ensure all values in the dictionary are numeric or have valid defaults."""
                    valid_data = {
                        key: value if is_numeric(value) else 0.0  # Default numeric fields to 0.0 if they are None
                        for key, value in data.items()
                    }

                    # Ensure the date field is set to a valid value, using current date as fallback
                    if 'date' in data:
                        if data['date'] is None:
                            valid_data['date'] = datetime.now().isoformat()
                        elif isinstance(data['date'], datetime):
                            valid_data['date'] = data['date'].isoformat()
                        elif isinstance(data['date'], str):
                            try:
                                # Validate the date string
                                datetime.fromisoformat(data['date'])
                                valid_data['date'] = data['date']
                            except ValueError:
                                self.logger.warning(f"Invalid date format for data: {data['date']}. Using current date.")
                                valid_data['date'] = datetime.now().isoformat()

                    return valid_data

                # Fetch Technical Indicators
                self.task_dict[ticker]["progress"] = "fetching technical indicators"
                self.logger.debug(f"Checking data freshness for technical indicators of {ticker}")
                fresh_technical_data = await self.check_data_freshness(ticker_instance, "technical_indicators")
                self.logger.debug(f"Data freshness for technical indicators of {ticker}: {fresh_technical_data}")

                if not fresh_technical_data:
                    self.logger.debug(f"Fetching technical indicators for {ticker}")
                    technical_indicators_data = await self.technical_indicators_fetcher.get_all_indicators(session, ticker)
                    self.logger.debug(f"Technical indicators data for {ticker}: {technical_indicators_data}")

                    if isinstance(technical_indicators_data, dict):
                        indicators_to_store = validate_numeric_fields({
                            "sma": technical_indicators_data.get('sma'),
                            "ema": technical_indicators_data.get('ema'),
                            "rsi": technical_indicators_data.get('rsi'),
                            "adx": technical_indicators_data.get('adx'),
                            "dema": technical_indicators_data.get('dema'),
                            "tema": technical_indicators_data.get('tema'),
                            "macd": technical_indicators_data.get('macd'),
                            "bollingerbands": technical_indicators_data.get('bollingerbands'),
                            "stochastic": technical_indicators_data.get('stochastic'),
                            "williams": technical_indicators_data.get('williams'),
                            "standarddeviation": technical_indicators_data.get('standarddeviation'),
                            "stdev": technical_indicators_data.get('stdev'),
                            "variance": technical_indicators_data.get('variance'),
                            "momentum": technical_indicators_data.get('momentum'),
                            "obv": technical_indicators_data.get('obv'),
                            "cci": technical_indicators_data.get('cci'),
                            "atr": technical_indicators_data.get('atr'),
                            "roc": technical_indicators_data.get('roc'),
                            "mfi": technical_indicators_data.get('mfi'),
                            "ultosc": technical_indicators_data.get('ultosc'),
                            "date": datetime.now(),  # Initially a datetime object
                            "period": self.period  # Updated to use class variable
                        })
                        self.logger.debug(f"Indicators to store for {ticker}: {indicators_to_store}")

                        # Convert 'date' to ISO format string if it's a datetime object
                        if 'date' in indicators_to_store:
                            if isinstance(indicators_to_store['date'], datetime):
                                indicators_to_store['date'] = indicators_to_store['date'].isoformat()
                            elif isinstance(indicators_to_store['date'], str):
                                # Validate the date string
                                try:
                                    datetime.fromisoformat(indicators_to_store['date'])
                                except ValueError:
                                    self.logger.warning(f"Invalid date format for ticker {ticker}. Using current date.")
                                    indicators_to_store['date'] = datetime.now().isoformat()

                        self.logger.debug(f"Updating or creating TechnicalIndicators for {ticker}")
                        await sync_to_async(TechnicalIndicators.objects.update_or_create)(
                            ticker=ticker_instance, defaults=indicators_to_store
                        )
                        self.task_dict[ticker]["result_data"]["technical_indicators"] = indicators_to_store


                # Fetch Historical Data
                self.task_dict[ticker]["progress"] = "fetching historical data"
                fresh_historical_data = await self.check_data_freshness(ticker_instance, "historical_price")

                if not fresh_historical_data:
                    historical_price = await self.historical_data_fetcher.process_tickers_async(session)

                    if isinstance(historical_price, list):
                        historical_to_store = [
                            validate_numeric_fields({
                                "date": entry.get('date'),
                                "open": entry.get('open'),
                                "high": entry.get('high'),
                                "low": entry.get('low'),
                                "close": entry.get('close'),
                                "adj_close": entry.get('adj_close'),
                                "volume": entry.get('volume'),
                                "unadjusted_volume": entry.get('unadjusted_volume'),
                                "change": entry.get('change'),
                                "change_percent": entry.get('change_percent'),
                                "vwap": entry.get('vwap'),
                                "label": entry.get('label'),
                                "change_over_time": entry.get('change_over_time')
                            }) for entry in historical_price
                        ]
                        await sync_to_async(HistoricalPrice.objects.bulk_create)(historical_to_store)
                        self.task_dict[ticker]["result_data"]["historical_price"] = historical_to_store

                # Fetch Financial Scores
                self.task_dict[ticker]["progress"] = "fetching financial scores"
                fresh_financial_scores = await self.check_data_freshness(ticker_instance, "financial_scores")
                if not fresh_financial_scores:
                    financial_scores = await self.financial_scores.get_financial_scores(session)

                    if isinstance(financial_scores, dict):
                        financial_scores_to_store = validate_numeric_fields({
                            "altman_z_score": financial_scores.get('altman_z_score'),
                            "piotroski_score": financial_scores.get('piotroski_score'),
                            "working_capital": financial_scores.get('working_capital'),
                            "total_assets": financial_scores.get('total_assets'),
                            "retained_earnings": financial_scores.get('retained_earnings'),
                            "ebit": financial_scores.get('ebit'),
                            "market_cap": financial_scores.get('market_cap'),
                            "total_liabilities": financial_scores.get('total_liabilities'),
                            "revenue": financial_scores.get('revenue'),
                            "created_at": datetime.now()
                        })
                        await sync_to_async(FinancialScores.objects.update_or_create)(
                            ticker=ticker_instance, defaults=financial_scores_to_store
                        )
                        self.task_dict[ticker]["result_data"]["financial_scores"] = financial_scores_to_store

                # Fetch Financial Ratios
                self.task_dict[ticker]["progress"] = "fetching financial ratios"
                fresh_financial_ratios = await self.check_data_freshness(ticker_instance, "financial_ratios")
                if not fresh_financial_ratios:
                    financial_ratios = await self.financial_ratios.process_tickers_FR_async(session)

                    if isinstance(financial_ratios, dict):
                        financial_ratios_to_store = validate_numeric_fields({
                            "current_ratio": financial_ratios.get('current_ratio'),
                            "quick_ratio": financial_ratios.get('quick_ratio'),
                            "cash_ratio": financial_ratios.get('cash_ratio'),
                            "gross_profit_margin": financial_ratios.get('gross_profit_margin'),
                            "operating_profit_margin": financial_ratios.get('operating_profit_margin'),
                            "pretax_profit_margin": financial_ratios.get('pretax_profit_margin'),
                            "net_profit_margin": financial_ratios.get('net_profit_margin'),
                            "effective_tax_rate": financial_ratios.get('effective_tax_rate'),
                            "return_on_assets": financial_ratios.get('return_on_assets'),
                            "return_on_equity": financial_ratios.get('return_on_equity'),
                            "debt_ratio": financial_ratios.get('debt_ratio'),
                            "debt_equity_ratio": financial_ratios.get('debt_equity_ratio'),
                            "created_at": datetime.now()
                        })
                        await sync_to_async(FinancialRatios.objects.update_or_create)(
                            ticker=ticker_instance, defaults=financial_ratios_to_store
                        )
                        self.task_dict[ticker]["result_data"]["financial_ratios"] = financial_ratios_to_store

                # Fetch Real-Time Data
                self.task_dict[ticker]["progress"] = "fetching real-time data"
                fresh_real_time_data = await self.check_data_freshness(ticker_instance, "real_time_price")
                if not fresh_real_time_data:
                    real_time_data = await self.real_time_data_fetcher.fetch_data_for_multiple_tickers(session)

                    if isinstance(real_time_data, dict):
                        real_time_to_store = validate_numeric_fields({
                            "bid_size": real_time_data.get('bid_size'),
                            "ask_price": real_time_data.get('ask_price'),
                            "volume": real_time_data.get('volume'),
                            "ask_size": real_time_data.get('ask_size'),
                            "bid_price": real_time_data.get('bid_price'),
                            "last_sale_price": real_time_data.get('last_sale_price'),
                            "last_sale_size": real_time_data.get('last_sale_size'),
                            "last_sale_time": real_time_data.get('last_sale_time'),
                            "fmp_last": real_time_data.get('fmp_last'),
                            "last_updated": real_time_data.get('last_updated'),
                            "created_at": datetime.now()
                        })
                        await sync_to_async(RealTimePrice.objects.update_or_create)(
                            ticker=ticker_instance, defaults=real_time_to_store
                        )
                        self.task_dict[ticker]["result_data"]["real_time_price"] = real_time_to_store

                # Fetch News Data
                self.task_dict[ticker]["progress"] = "fetching news data"
                fresh_news_data = await self.check_data_freshness(ticker_instance, "news")
                if not fresh_news_data:
                    news_data = await self.news_getter.store_news()
                    if isinstance(news_data, list):
                        classified_news = await self.news_classifier.run_news_classification(news_data)
                        if classified_news:
                            news_to_store = {
                                "news_data": classified_news,
                                "created_at": datetime.now()
                            }
                            await sync_to_async(NewsData.objects.update_or_create)(
                                ticker=ticker_instance, defaults=news_to_store
                            )
                            self.task_dict[ticker]["result_data"]["news"] = news_to_store

                # Fetch Forecast Data
                self.task_dict[ticker]["progress"] = "fetching forecast data"
                fresh_forecast_data = await self.check_data_freshness(ticker_instance, "prophet_forecast")
                if not fresh_forecast_data:
                    forecast, X_test, y_test, xgb_forecast = await self.forecaster.runPF()
                    if isinstance(forecast, dict):
                        forecast_data_to_store = {
                            "forecast": forecast,
                            "X_test": X_test,
                            "y_test": y_test,
                            "xgb_forecast": xgb_forecast,
                            "created_at": datetime.now()
                        }
                        await sync_to_async(DayTimeForecaster.objects.update_or_create)(
                            ticker=ticker_instance, defaults=forecast_data_to_store
                        )
                        self.task_dict[ticker]["result_data"]["prophet_forecast"] = forecast_data_to_store

            except Exception as e:
                self.task_dict[ticker]["status"] = "FAILED"
                self.task_dict[ticker]["error_message"] = str(e)
                self.logger.error(f"Error processing data for {ticker}: {e}")
            finally:
                self.task_dict[ticker]["status"] = "COMPLETED"
                self.task_dict[ticker]["end_time"] = datetime.now()
                self.logger.info(f"Task for ticker '{ticker}' finalized with status {self.task_dict[ticker]['status']}.")