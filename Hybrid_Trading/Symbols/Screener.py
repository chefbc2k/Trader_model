import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
import json  # Keep it for future use in serializing/deserializing

# Load environment variables
load_dotenv()

# Initialize the LoggingMaster
logger = LoggingMaster("StockScreener").get_logger()

# Retrieve the API key from environment variables
FMP_API_KEY = os.getenv('FMP_API_KEY')

class StockScreener:
    """A class to interact with Financial Modeling Prep API for stock screening."""
    
    SCREENER_URL = "https://financialmodelingprep.com/api/v3/stock-screener"

    def __init__(self, market_cap_more_than=50_000_000, market_cap_lower_than=None, beta_more_than=0.5, 
                 beta_lower_than=1.5, volume_more_than=50_000, volume_lower_than=None, 
                 price_more_than=1, price_lower_than=100, dividend_more_than=0, dividend_lower_than=5,
                 country="US", is_etf=False, is_actively_trading=True):
        self.params: Dict[str, Any] = {
            "marketCapMoreThan": str(market_cap_more_than),
            "marketCapLowerThan": str(market_cap_lower_than) if market_cap_lower_than is not None else None,
            "betaMoreThan": str(beta_more_than),
            "betaLowerThan": str(beta_lower_than),
            "volumeMoreThan": str(volume_more_than),
            "volumeLowerThan": str(volume_lower_than) if volume_lower_than is not None else None,
            "priceMoreThan": str(price_more_than),
            "priceLowerThan": str(price_lower_than),
            "dividendMoreThan": str(dividend_more_than),
            "dividendLowerThan": str(dividend_lower_than),
            "country": str(country),
            "isEtf": str(is_etf).lower(),
            "isActivelyTrading": str(is_actively_trading).lower(),
            "limit": "100",  # Fetch 100 stocks per API call to process more stocks per day
            "apikey": str(FMP_API_KEY)  # Include the API key here
        }

    def fetch_stocks(self) -> List[str]:
        """Fetch stocks based on the initialized parameters and return their symbols as strings."""
        logger.info(f"Fetching stocks with parameters: {self.params}")
        
        try:
            response = requests.get(self.SCREENER_URL, params=self.params, timeout=10)
            response.raise_for_status()  # This will raise an HTTPError if the status is not 200
            data = response.json()  # This is already JSON formatted, no need for the json module to parse
            
            if isinstance(data, list):
                logger.info(f"Fetched {len(data)} stocks.")
                return [str(stock['symbol']) for stock in data]
            else:
                logger.error(f"Unexpected data format for stock screener: {data}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching stocks: {e}")
            return []

    def run_screener(self, total_days=5, max_workers=10):
        """Run the screener daily for a given number of days to cover a wide range of stocks."""
        logger.info(f"Starting stock screener for {total_days} days.")
        
        for day in range(total_days):
            logger.info(f"Day {day + 1} of {total_days}")
            
            # Fetch stocks
            stock_symbols = self.fetch_stocks()
            
            # Process stocks in parallel using ThreadPoolExecutor
            if stock_symbols:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(self.process_stock, symbol): symbol for symbol in stock_symbols}
                    for future in as_completed(futures):
                        symbol = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error processing stock {symbol}: {e}")
            
            logger.info(f"Completed day {day + 1} of stock screening.")

        logger.info("Stock screening process completed.")

    def process_stock(self, symbol: str):
        """Process individual stock data."""
        # Placeholder for processing each stock symbol
        logger.info(f"Processing stock: {symbol}")

# Example usage
if __name__ == "__main__":
    screener = StockScreener()
    screener.run_screener(total_days=7, max_workers=10)