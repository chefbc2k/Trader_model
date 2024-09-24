import os
import random
import asyncio
from datetime import datetime
import aiohttp
from tqdm.asyncio import tqdm
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Set up logging using LoggingMaster
logger = LoggingMaster("FinancialRatiosTTM").get_logger()

class FinancialRatios:
    """
    The FinancialRatios class is responsible for fetching financial ratio data for the trailing twelve months (TTM) from the FMP API.
    This class focuses on data fetching, storing the results in CDS, and retrieving any existing data.
    """

    def __init__(self, tickers):
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        if not self.fmp_api_key:
            raise ValueError("FMP API Key is not set. Please set it in your environment variables.")
        
        self.ticker = tickers
        self.base_url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{self.ticker}"

    async def fetch_financial_ratios(self, session: aiohttp.ClientSession) -> dict:
        """
        Fetch financial ratios from the FMP API for the given ticker.
        Interacts with CDS to store and retrieve data.

        Args:
            session (aiohttp.ClientSession): The HTTP session used to fetch data.

        Returns:
            dict: The fetched financial ratios in JSON format.
        """

        # Check if the data is already stored in CDS
        stored_ratios = await self.cds.retrieve(self.ticker, "financial_ratios")# Make sure to await CDS retrieval
        if stored_ratios:
            logger.info(f"Using cached financial ratios for {self.ticker} from CDS")
            return stored_ratios

        # Correct API endpoint format
        url = f"{self.base_url}?apikey={self.fmp_api_key}"
        logger.info(f"Fetching financial ratios (TTM) for {self.ticker}")

        try:
            async with session.get(url, timeout=15) as response:
                response.raise_for_status()
                ratios = await response.json()

                if ratios:
                    logger.info(f"Successfully fetched financial ratios (TTM) for {self.ticker}")

                    # Store the fetched ratios in CDS
                    await self.cds.store(self.ticker, "financial_ratios_ttm", ratios)  # Ensure storage is awaited
                    await self.cds.store(self.ticker, "last_fetched_financial_ratios_ttm", datetime.now().isoformat())

                    return ratios
                else:
                    logger.warning(f"No financial ratios found for {self.ticker}")
                    return {}
        
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching financial ratios for {self.ticker}: {e}")
            return {}

        # Asynchronous function to process multiple tickers
    async def process_tickers_FR_async(tickers: list, cds):
            """
            This function processes multiple tickers by fetching financial ratio data for each one.
            It interacts with the provided CDS instance.

            Args:
                tickers (list): List of stock tickers to process.
                cds: An instance of CentralizedDataStorage.

            Returns:
                list: A list of dictionaries containing financial ratios for each ticker.
            """

            async with aiohttp.ClientSession() as session:
                tasks = []
                for ticker in tickers:
                    fr = FinancialRatios(ticker, cds)
                    task = asyncio.create_task(fr.fetch_financial_ratios(session))  # Ensure that fetch_financial_ratios is awaited
                    tasks.append(task)

                results = []
                for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching Financial Ratios", unit="ticker"):
                    result = await task
                    results.append(result)
                    if not result:
                        logger.warning(f"Failed to fetch financial ratios for a ticker")

                return results