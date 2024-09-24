import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from tqdm.asyncio import tqdm
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

logger = LoggingMaster("HistoricalData").get_logger()

class HistoricalData:
    MAX_RETRIES = 3  # Maximum number of retries for fetching data

    # The columns as they appear in the API response
    REQUIRED_COLUMNS_HISTORICAL = [
        'date', 'open', 'high', 'low', 'close', 'volume', 'ticker',
        'adjClose', 'unadjustedVolume', 'change', 'changePercent',
        'vwap', 'label', 'changeOverTime'
    ]

    # Mapping from API field names (camelCase) to Django model field names (snake_case)
    FIELD_MAPPING = {
        'adjClose': 'adj_close',
        'unadjustedVolume': 'unadjusted_volume',
        'changeOverTime': 'change_over_time',
        'changePercent': 'change_percent'
    }

    def __init__(self, tickers: str, start_date: str, end_date: str, interval: str, period: str, cds=None, missing_value_strategy: str = 'fill', fillna_method: str = 'zero'):
        """
        Initialize the HistoricalData class with necessary parameters.
        """
        self.ticker = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.period = period
        self.cds = cds  # CDS instance for storage/retrieval
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        self.missing_value_strategy = missing_value_strategy
        self.fillna_method = fillna_method

    async def get_available_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch available date range for the given ticker.
        """
        params = {
            'apikey': self.fmp_api_key,
            'serietype': 'candle'
        }
        
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{self.ticker}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if 'historical' in data and len(data['historical']) > 0:
                        latest_date = data['historical'][0]['date']
                        earliest_date = data['historical'][-1]['date']
                        return earliest_date, latest_date
                    else:
                        logger.error(f"No historical data found for {self.ticker}.")
                        return None, None
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching available date range for {self.ticker}: {e}.")
            return None, None

    async def adjust_date_range(self) -> List[Tuple[str, str]]:
        """
        Adjust the date range to ensure it is within the available range from the API.
        """
        earliest_date, latest_date = await self.get_available_date_range()
        if earliest_date is None or latest_date is None:
            logger.error(f"Unable to find available date range for {self.ticker}.")
            return []

        requested_start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        requested_end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        available_start_date = datetime.strptime(earliest_date, "%Y-%m-%d")
        available_end_date = datetime.strptime(latest_date, "%Y-%m-%d")

        if requested_start_date < available_start_date:
            requested_start_date = available_start_date
        if requested_end_date > available_end_date:
            requested_end_date = available_end_date

        date_ranges = []
        current_start_date = requested_start_date

        while current_start_date <= requested_end_date:
            current_end_date = current_start_date + timedelta(days=1825)
            if current_end_date > requested_end_date:
                current_end_date = requested_end_date

            date_ranges.append((current_start_date.strftime("%Y-%m-%d"), current_end_date.strftime("%Y-%m-%d")))
            current_start_date = current_end_date + timedelta(days=1)

        return date_ranges

    async def get_historical_data(self, session: aiohttp.ClientSession) -> List[dict]:
        """
        Fetch historical data for the specified ticker and date range.
        """
        # Check if data is available in CDS (if provided)
        if self.cds:
            cached_data = await self.cds.retrieve(self.ticker, "historical_data")
            if cached_data:
                logger.info(f"Using cached historical data for {self.ticker} from CDS")
                return cached_data if isinstance(cached_data, list) else []

        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{self.ticker}?from={self.start_date}&to={self.end_date}&apikey={self.fmp_api_key}"

        for attempt in range(self.MAX_RETRIES):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if 'historical' in data and len(data['historical']) > 0:
                        all_data = []
                        for record in data['historical']:
                            cleaned_record = self.clean_record(record)
                            all_data.append(cleaned_record)

                        # Store data in CDS (if provided)
                        if self.cds:
                            await self.cds.store(self.ticker, "historical_data", all_data)

                        return all_data  # Return the list of historical data records
                    else:
                        logger.warning(f"No historical data returned for {self.ticker} in API response.")
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching historical data for {self.ticker} from API: {e}. Attempt {attempt + 1}/{self.MAX_RETRIES}")

        logger.error(f"Failed to fetch historical data for {self.ticker} after {self.MAX_RETRIES} attempts.")
        return []  # Return an empty list on failure

    def clean_record(self, record: dict) -> dict:
        """
        Clean and map API record fields to match the Django model.
        """
        cleaned_record = {}

        # Map fields from camelCase to snake_case
        for api_field, model_field in self.FIELD_MAPPING.items():
            cleaned_record[model_field] = record.get(api_field, 0)

        # Copy over fields that don't require mapping
        cleaned_record.update({
            'date': record.get('date', self.start_date),
            'open': record.get('open', 0),
            'high': record.get('high', 0),
            'low': record.get('low', 0),
            'close': record.get('close', 0),
            'volume': record.get('volume', 0),
            'ticker': self.ticker,  # Add the ticker symbol
            'vwap': record.get('vwap', 0),
            'label': record.get('label', ''),
        })

        return cleaned_record

    # Asynchronous function to process multiple tickers
    @staticmethod
    async def process_tickers_async(tickers: List[str], start_date: str, end_date: str, cds=None) -> List[dict]:
        """
        Process historical data for multiple tickers asynchronously.
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            for ticker in tickers:
                hd = HistoricalData(ticker, start_date, end_date, interval="1d", period="D", cds=cds)
                task = asyncio.create_task(hd.get_historical_data(session))
                tasks.append(task)

            results = []
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching historical data"):
                result = await task
                results.append(result)
                if not result:
                    logger.warning(f"Failed to fetch historical data for {ticker}")
                else:
                    logger.info(f"Successfully fetched and processed historical data for {ticker}")

            return results