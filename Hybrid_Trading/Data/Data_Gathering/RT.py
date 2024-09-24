import os
import asyncio
import aiohttp
from datetime import datetime
from tqdm.asyncio import tqdm
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from typing import Dict, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging using LoggingMaster
logger = LoggingMaster("RealTimeDataGatherer").get_logger()

# Define the required columns for real-time data
REQUIRED_COLUMNS_REAL_TIME = [
    'bid_price', 'ask_price', 'volume', 'bid_size', 'ask_size', 
    'last_sale_price', 'last_sale_size', 'last_sale_time', 'last_updated', 'ticker'
]

class RealTimeData:
    def __init__(self, tickers: str):
        """
        Initialize with just the ticker, no longer referencing cds or user_input.
        """
        self.ticker = tickers
        self.fmp_api_key = os.getenv('FMP_API_KEY')  # Load API key from environment variables
        if not self.fmp_api_key:
            raise ValueError("FMP API Key is not set. Please ensure it is defined in your .env file.")

    async def fetch_real_time_data(self, session: aiohttp.ClientSession) -> dict:
        """
        Fetch real-time stock data from the Financial Modeling Prep API endpoint.
        """
        url = f"https://financialmodelingprep.com/api/v3/stock/full/real-time-price/{self.ticker}?apikey={self.fmp_api_key}"
        logger.info(f"Fetching real-time data for {self.ticker}.")

        try:
            async with session.get(url, timeout=15) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    # Handle the case where data is a dictionary
                    data = self.standardize_columns(data, REQUIRED_COLUMNS_REAL_TIME)
                    logger.info(f"Fetched real-time data for {self.ticker}.")
                    return data
                elif isinstance(data, list) and len(data) > 0:
                    # Handle the case where data is a list with a single dictionary entry
                    standardized_data = self.standardize_columns(data[0], REQUIRED_COLUMNS_REAL_TIME)
                    logger.info(f"Fetched real-time data for {self.ticker}.")
                    return standardized_data
                else:
                    logger.warning(f"No valid real-time data returned for {self.ticker}.")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching real-time data for {self.ticker}: {e}")
            return {}

    def standardize_columns(self, data: dict, required_columns: List[str]) -> dict:
        """
        Ensure the data has the required columns with correct names.
        If some columns are missing, fill them with a default value to avoid issues during processing.
        """
        # Use a default value of 0 for numerical data and an empty string for text fields
        default_values = {
            'bid_price': 0.0,
            'ask_price': 0.0,
            'volume': 0,
            'bid_size': 0,
            'ask_size': 0,
            'last_sale_price': 0.0,
            'last_sale_size': 0,
            'last_sale_time': '',
            'last_updated': '',
            'ticker': self.ticker
        }

        standardized_data = {col: data.get(col, default_values.get(col)) for col in required_columns}
        return standardized_data

    @staticmethod
    async def fetch_data_for_multiple_tickers(tickers: List[str]) -> Dict[str, dict]:
        """
        Fetch real-time data for multiple tickers using asyncio.
        """
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for ticker in tickers:
                real_time_data = RealTimeData(ticker)
                tasks.append(real_time_data.fetch_real_time_data(session))
            
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching real-time data"):
                try:
                    data = await task
                    ticker = tickers[tasks.index(task)]  # Get the ticker corresponding to this task
                    results[ticker] = data
                except Exception as e:
                    logger.error(f"Error processing data for {ticker}: {e}")
                    results[ticker] = {}

        return results