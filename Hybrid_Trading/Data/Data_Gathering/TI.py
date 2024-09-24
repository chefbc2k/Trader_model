from datetime import datetime
import os
import logging
import aiohttp
import asyncio
from typing import Dict, List
from dotenv import load_dotenv
from tqdm.asyncio import tqdm
from Config.trading_constants import TCS

# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='tech_indicators.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TechnicalIndicatorFetcher:
    def __init__(self, constants: TCS, tickers: List[str], start_date: str, end_date: str, interval: str, period: int, cds=None):
        """
        Initialize the TechnicalIndicatorFetcher with necessary parameters.
        """
        self.constants = constants
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.period = period
        self.cds = cds  # Centralized Data Storage instance

        # Load API key from environment variables
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY is missing from the environment variables.")

        logging.info("TechnicalIndicatorFetcher initialized successfully with tickers, start_date, end_date, interval, and period.")

    async def fetch_indicator(self, session: aiohttp.ClientSession, ticker: str, indicator: str) -> Dict[str, float]:
        """Fetch a specific technical indicator for a given ticker."""
        # Check if data is available in CDS (if provided)
        if self.cds:
            cached_data = await self.cds.retrieve(ticker, indicator)
            if cached_data:
                logging.info(f"Using cached data for {ticker} - {indicator} from CDS")
                return {indicator: cached_data}

        # Build the API endpoint with correct path and query parameters
        endpoint = f"https://financialmodelingprep.com/api/v3/technical_indicator/{self.interval}/{ticker}?type={indicator}&period={self.period}&apikey={self.api_key}&from={self.start_date}&to={self.end_date}"

        logging.info(f"Fetching {indicator} for {ticker} at interval {self.interval} from {self.start_date} to {self.end_date}.")

        try:
            async with session.get(endpoint, timeout=15) as response:
                response.raise_for_status()
                data = await response.json()

                if data:
                    latest_data = data[0]  # Assuming the first entry is the latest
                    indicator_value = latest_data.get(indicator, 0.0)
                    logging.info(f"Fetched {indicator} for {ticker}: {indicator_value}")

                    # Optionally store the fetched data in CDS
                    if self.cds:
                        await self.cds.store(ticker, indicator, indicator_value)

                    # Handle 'date' field if present
                    if 'date' in latest_data:
                        date_value = latest_data.get('date')
                        if isinstance(date_value, datetime):
                            latest_data['date'] = date_value.isoformat()
                        elif isinstance(date_value, str):
                            try:
                                datetime.fromisoformat(date_value)
                            except ValueError:
                                logging.warning(f"Invalid date format for {ticker}. Using current date.")
                                latest_data['date'] = datetime.now().isoformat()

                    return {indicator: indicator_value}

                logging.warning(f"No data found for {indicator} on {ticker}. Returning 0.0")
                return {indicator: 0.0}

        except aiohttp.ClientError as e:
            logging.error(f"Error fetching {indicator} for {ticker}: {e}")
            return {indicator: 0.0}
        except Exception as e:
            logging.error(f"Unexpected error fetching {indicator} for {ticker}: {e}")
            return {indicator: 0.0}
        
    async def get_all_indicators(self, session: aiohttp.ClientSession, ticker: str) -> Dict[str, float]:
        """Fetch all indicators for a given ticker."""
        logging.info(f"Getting all indicators for {ticker}...")
        results = {}
        indicators = list(self.constants.INDICATORS.keys())

        tasks = [
            asyncio.create_task(self.fetch_indicator(session, ticker, indicator))
            for indicator in indicators
        ]

        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=f"Processing {ticker} indicators"):
            try:
                result = await task
                results.update(result)
                logging.info(f"Indicator {list(result.keys())[0]} for {ticker} processed: {result[list(result.keys())[0]]}")
            except Exception as e:
                logging.error(f"Error processing indicator task for {ticker}: {e}")

        logging.info(f"Completed fetching indicators for {ticker}: {results}")
        return results

    async def fetch_indicators_for_tickers(self, tickers: List[str], session: aiohttp.ClientSession) -> Dict[str, Dict[str, float]]:
        """Fetch technical indicators for a list of tickers using an active session."""
        all_indicators = {}

        # Create tasks for fetching indicators, and store each task along with its corresponding ticker
        tasks = [asyncio.create_task(self.get_all_indicators(session, ticker)) for ticker in tickers]

        # Iterate over the completed tasks as they finish
        for completed_task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching Technical Indicators"):
            try:
                result = await completed_task

                # Fetch the index of the completed task to get the associated ticker
                ticker = tickers[tasks.index(completed_task)]

                if result:
                    all_indicators[ticker] = result
                else:
                    logging.warning(f"Failed to fetch indicators for {ticker}")
            except Exception as e:
                logging.error(f"Error processing task for ticker {ticker}: {e}")

        logging.info(f"Fetched technical indicators for all tickers: {all_indicators}")
        return all_indicators