import pandas as pd
import datetime
from typing import Dict, Any, List
from Config.trading_constants import TCS
from Hybrid_Trading.Log.Logging_Master import LoggingMaster  # Correctly imported LoggingMaster
from Config.utils import TempFiles
from asgiref.sync import sync_to_async
from Hybrid_Trading.Data.models import FinancialScores, TechnicalIndicators, RealTimePrice  # Added necessary models

class DynamicStrategy:
    def __init__(
        self, 
        ticker: str, 
        prophet_forecast: pd.DataFrame,  
        constants: TCS, 
        user_input: Any, 
        temp_files: TempFiles,
    ):
        self.ticker = ticker
        self.start_date = user_input.start_date
        self.end_date = user_input.end_date
        self.prophet_forecast = prophet_forecast
        self.constants = constants
        self.user_input = user_input
        self.temp_files = temp_files

        # Initialize the logger from LoggingMaster
        self.logger = LoggingMaster("DynamicStrategy").get_logger()

        # Placeholders for fetched data
        self.real_time_data = None
        self.technical_indicators = None
        self.financial_scores = None

    async def fetch_data(self):
        """
        Fetch necessary data from the database, including real-time price, financial scores,
        and technical indicators.
        """
        try:
            # Fetch real-time price data from RealTimePrice model
            self.real_time_data = await sync_to_async(RealTimePrice.objects.filter(ticker=self.ticker).values)()

            # Fetch technical indicators from the TechnicalIndicators model
            self.technical_indicators = await sync_to_async(TechnicalIndicators.objects.filter(ticker=self.ticker).values)()

            # Fetch financial scores from the FinancialScores model
            self.financial_scores = await sync_to_async(FinancialScores.objects.filter(ticker=self.ticker).values)()

        except Exception as e:
            self.logger.error(f"Error fetching data for ticker {self.ticker}: {e}")

    async def apply_strategy(self):
        # Fetch the required data before proceeding with strategy logic
        await self.fetch_data()

        current_date = datetime.date.today()

        # Ensure that real-time data has the necessary columns
        if not self.real_time_data or 'last_sale_price' not in self.real_time_data[0]:
            self.logger.error(f"Real-time data for {self.ticker} does not contain 'last_sale_price'.")
            return {self.ticker: "Hold: Missing real-time price data."}

        current_price = self.real_time_data[0]['last_sale_price']

        # Fetch Prophet forecast for the current day
        predicted_today = self.prophet_forecast[self.prophet_forecast['ds'] == str(current_date)]['yhat'].values[0]

        # Prepare technical indicators
        indicators = {
            'ema': self.technical_indicators[0].get('ema') if self.technical_indicators else None,
            'wma': self.technical_indicators[0].get('wma') if self.technical_indicators else None,
            'sma': self.technical_indicators[0].get('sma') if self.technical_indicators else None,
            'tema': self.technical_indicators[0].get('tema') if self.technical_indicators else None,
            'dema': self.technical_indicators[0].get('dema') if self.technical_indicators else None,
            'williams': self.technical_indicators[0].get('williams') if self.technical_indicators else None,
            'rsi': self.technical_indicators[0].get('rsi') if self.technical_indicators else None,
            'std_dev': self.technical_indicators[0].get('standarddeviation') if self.technical_indicators else None,
            'adx': self.technical_indicators[0].get('adx') if self.technical_indicators else None
        }

        # Incorporate Financial Scores into the strategy
        if not self.financial_scores:
            self.logger.error(f"No financial scores found for {self.ticker}.")
            return {self.ticker: "Hold: Missing financial scores."}

        financial_health = self.financial_scores[0]['altman_z_score']
        if financial_health > self.constants.FINANCIAL_THRESHOLDS['good']:
            self.logger.info(f"Financial health for {self.ticker} is strong.")
        else:
            self.logger.info(f"Financial health for {self.ticker} is weak.")

        # Generate buy/sell signals based on price, indicators, and financial health
        buy_signals = 0
        if current_price < predicted_today and financial_health > self.constants.FINANCIAL_THRESHOLDS['good']:
            for indicator, value in indicators.items():
                if value is not None and value < self.constants.THRESHOLDS[indicator]['buy']:
                    buy_signals += 1
                    break
        else:
            for indicator, value in indicators.items():
                if value is not None and value < self.constants.THRESHOLDS[indicator]['buy']:
                    buy_signals += 1
            if buy_signals >= 3:
                buy_signals = 1

        sell_signals = 0
        if current_price > predicted_today:
            for indicator, value in indicators.items():
                if value is not None and value > self.constants.THRESHOLDS[indicator]['sell']:
                    sell_signals += 1
                    break
        else:
            for indicator, value in indicators.items():
                if value is not None and value > self.constants.THRESHOLDS[indicator]['sell']:
                    sell_signals += 1
            if sell_signals >= 3:
                sell_signals = 1

        # Make decision based on buy/sell signals
        if buy_signals:
            decision = f"Buy: Prediction is favorable, and {'one or more indicators' if current_price < predicted_today else 'three or more indicators'} support this decision."
        elif sell_signals:
            decision = f"Sell: Prediction is unfavorable, and {'one or more indicators' if current_price > predicted_today else 'three or more indicators'} support this decision."
        else:
            decision = "Hold: No strong buy or sell signal."

        self.logger.info(f"Strategy decision for {self.ticker}: {decision}")

        # Save the decision in the database or external storage
        await sync_to_async(self.temp_files.save_to_sheet)({self.ticker: decision}, "Strategy Decisions")

        return {self.ticker: decision}

    async def run(self):
        self.logger.info(f"Running dynamic strategy for {self.ticker}...")
        decision = await self.apply_strategy()

        # Save Prophet forecast and strategy decisions to the database
        await sync_to_async(self.temp_files.save_to_sheet)({self.ticker: self.prophet_forecast}, "Prophet Forecast")
        await sync_to_async(self.temp_files.save_to_sheet)({self.ticker: decision}, "Strategy Decisions")

        self.logger.info(f"Dynamic strategy for {self.ticker} completed.")
        return decision