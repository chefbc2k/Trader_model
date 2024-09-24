import logging
import os
import pandas as pd
import requests
import asyncio
import aiohttp
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from Hybrid_Trading.Inputs.user_input import UserInput
from functools import lru_cache

class MTDataFetcher:
    def __init__(self, user_input: UserInput):
        load_dotenv()
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.user_input = user_input
        
    def standardize_columns(self, df):
        """Standardize column names to ensure consistency."""
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.strip()
        return df

    def calculate_date_range(self):
        """Calculate the start and end dates based on user input for interval and duration."""
        interval = self.user_input.args.get('interval', '1d')
        duration = self.user_input.args.get('duration', '1y')
        period = self.user_input.args.get('period', 'day')
        
        end_date = datetime.now()
        start_date = self._get_start_date_based_on_duration(duration, end_date)
        self.user_input.args['start_date'] = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        self.user_input.args['end_date'] = end_date.strftime('%Y-%m-%d')
        return start_date, end_date

    def _get_start_date_based_on_duration(self, duration, end_date):
        if duration == '1m':
            return end_date - timedelta(days=30)
        elif duration == '3m':
            return end_date - timedelta(days=90)
        elif duration == '6m':
            return end_date - timedelta(days=180)
        elif duration == '1y':
            return end_date - timedelta(days=365)
        elif duration == '5y':
            return end_date - timedelta(days=1825)
        elif duration == '10y':
            return end_date - timedelta(days=3650)
        elif duration == '20y':
            return end_date - timedelta(days=7300)
        elif duration == 'all':
            return '1900-01-01'
        else:
            raise ValueError("Invalid duration.")

    @lru_cache(maxsize=100)
    def fetch_data_from_cache(self, url):
        """Simple in-memory cache for API requests to avoid repeated calls."""
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    async def async_fetch(self, session, url, delay=0):
        """Asynchronous fetch with optional jitter delay."""
        await asyncio.sleep(delay)  # Apply jitter
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    def apply_jitter(self):
        """Random delay to avoid rate limits."""
        return random.uniform(0.1, 0.5)  # Random jitter between 100ms and 500ms

    async def fetch_all_async(self, ticker, urls):
        """Fetch all data asynchronously for a ticker."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, url in urls.items():
                delay = self.apply_jitter()  # Apply jitter to each request
                tasks.append(self.async_fetch(session, url, delay))
            results = await asyncio.gather(*tasks)
            return dict(zip(urls.keys(), results))

    def validate_data(self, data: pd.DataFrame):
        """Basic validation to ensure data is not empty and columns are standardized."""
        if data.empty:
            logging.error("Data validation failed: DataFrame is empty.")
            raise ValueError("Data validation failed: DataFrame is empty.")
        
        # Standardize column names
        data = self.standardize_columns(data)
        logging.info("Data validation passed.")
        return data

    def fetch_and_preprocess_data_all_sources(self, ticker: str) -> pd.DataFrame:
        """Fetch data from all sources for a ticker."""
        if 'start_date' not in self.user_input.args or 'end_date' not in self.user_input.args:
            self.calculate_date_range()

        urls = {
            'historical_data': f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={self.user_input.args['start_date']}&to={self.user_input.args['end_date']}&apikey={self.fmp_api_key}",
            'financial_ratios': f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={self.fmp_api_key}",
            'key_metrics': f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?apikey={self.fmp_api_key}",
            'upgrades_downgrades': f"https://financialmodelingprep.com/api/v4/upgrades-downgrades-consensus?symbol={ticker}&apikey={self.fmp_api_key}",
            'historical_interday': f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{ticker}?apikey={self.fmp_api_key}"
        }

        # Asynchronously fetch all data
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.fetch_all_async(ticker, urls))

        # Process and merge the data
        data_sources = {
            'historical_data': pd.DataFrame(results['historical_data']['historical']).add_prefix('historical_'),
            'financial_ratios': pd.DataFrame(results['financial_ratios']).add_prefix('ratios_'),
            'key_metrics': pd.DataFrame(results['key_metrics']).add_prefix('metrics_'),
            'upgrades_downgrades': pd.DataFrame(results['upgrades_downgrades']).add_prefix('upgrades_downgrades_'),
            'historical_interday': pd.DataFrame(results['historical_interday']).add_prefix('interday_')
        }

        # Combine all data on 'ticker' and 'date'
        combined_data = pd.concat(data_sources.values(), axis=1, join='outer')

        # Basic validation to ensure combined data is not empty
        if combined_data.empty:
            logging.warning(f"No data returned after combining all sources for {ticker}.")
            return pd.DataFrame()

        logging.info(f"Combined data for {ticker}:\n{combined_data.head()}")
        return combined_data