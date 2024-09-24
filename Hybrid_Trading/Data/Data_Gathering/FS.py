import os
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Load environment variables
load_dotenv()

# Initialize the LoggingMaster
logger = LoggingMaster("FinancialScores").get_logger()

# Retrieve the API key from environment variables
FMP_API_KEY = os.getenv('FMP_API_KEY')

class FinancialScores:
    """A class to interact with Financial Modeling Prep API for Financial Scores (Altman Z-Score, Piotroski Score)."""

    FINANCIAL_SCORE_URL = "https://financialmodelingprep.com/api/v4/score"

    def __init__(self, tickers: str):
        """
        Initialize with ticker.
        """
        self.ticker = tickers  # Store the ticker symbol

    async def get_financial_scores(self, session: aiohttp.ClientSession, retry_attempts: int = 3) -> dict:
        """Fetch financial scores, retrying on failure."""
        url = f"{self.FINANCIAL_SCORE_URL}?symbol={self.ticker}&apikey={FMP_API_KEY}"  # Include API key in the URL

        for attempt in range(retry_attempts):
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Convert and map field names to match Django model field names
                    if isinstance(data, list) and len(data) > 0:
                        mapped_data = self.map_to_django_fields(data[0])  # Map fields here
                        return mapped_data
                    else:
                        logger.warning(f"Unexpected data format for financial scores for {self.ticker}: {data}")
                        return {}

            except aiohttp.ClientError as e:
                logger.error(f"Error fetching data for {self.ticker} on attempt {attempt + 1}/{retry_attempts}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff on retries

        logger.error(f"All attempts to fetch financial scores for {self.ticker} failed. Returning default value.")
        return {}

    def map_to_django_fields(self, api_data: dict) -> dict:
        """Map API field names to Django model field names."""
        mapping = {
            'altmanZScore': 'altman_z_score',
            'piotroskiScore': 'piotroski_score',
            'workingCapital': 'working_capital',
            'totalAssets': 'total_assets',
            'retainedEarnings': 'retained_earnings',
            'ebit': 'ebit',
            'marketCap': 'market_cap',
            'totalLiabilities': 'total_liabilities',
            'revenue': 'revenue',
            'symbol': 'ticker'  # Map 'symbol' from API to 'ticker' in your Django model
        }
        
        return {mapping.get(key, key): value for key, value in api_data.items()}


class FinancialInsights:
    """A class to encapsulate the generation of insights for a given stock ticker, focusing on financial health using Altman Z-Score and Piotroski Score."""
    
    def __init__(self, ticker: str, start_date: str, end_date: str):
        """
        Initialize with ticker, start_date, and end_date.
        """
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.financial_scores = None
        self.financial_score_api = FinancialScores(ticker)  # Initialize with ticker only

        # Initialize a logger for this instance
        self.logger = LoggingMaster(f"FinancialInsights-{self.ticker}").get_logger()

    async def fetch_additional_data(self, session: aiohttp.ClientSession):
        """
        Fetch financial scores asynchronously using the FinancialScores API.
        """
        try:
            self.financial_scores = await self.financial_score_api.get_financial_scores(session)  # Ensure this is awaited
        except Exception as e:
            self.logger.error(f"Failed to fetch financial scores for {self.ticker}: {e}")
            self.financial_scores = {}  # Default to an empty dict

    def generate_insights(self) -> Dict[str, Any]:
        """Generate insights based on financial scores."""
        altman_z_score = self.financial_scores.get('altman_z_score', 0)
        piotroski_score = self.financial_scores.get('piotroski_score', 0)

        insights = {
            "Ticker Symbol": self.ticker,
            "Altman Z-Score": altman_z_score,
            "Piotroski Score": piotroski_score,
            "Insight Final Signal": self.determine_final_signal(altman_z_score, piotroski_score),  # Consolidated naming
            "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.logger.info(f"Insights generated for {self.ticker}: {insights}")
        return insights

    def determine_final_signal(self, altman_z_score: float, piotroski_score: int) -> Dict[str, Any]:
        """Determine the final signal based on the Altman Z-Score and Piotroski Score."""
        if altman_z_score > 2.99 and piotroski_score >= 8:
            return {"final_signal": "Buy", "altman_z_score": altman_z_score, "piotroski_score": piotroski_score}
        elif altman_z_score < 1.81 or piotroski_score <= 2:
            return {"final_signal": "Sell", "altman_z_score": altman_z_score, "piotroski_score": piotroski_score}
        else:
            return {"final_signal": "Hold", "altman_z_score": altman_z_score, "piotroski_score": piotroski_score}