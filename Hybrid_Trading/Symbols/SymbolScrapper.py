import requests
import logging
import json
import os
import sys
from datetime import datetime
from typing import Any, List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the directory containing Config to sys.path
sys.path.append('/Users/chefsbae/TB3 copy')

from Config.trading_constants import TCS
from Hybrid_Trading.Symbols.Screener import StockScreener  # Import StockScreener from the appropriate module

# Configure logging
logging.basicConfig(filename='scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FMPDataFetcher:
    """
    A class to interact with Financial Modeling Prep API.
    """
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    API_KEY = str(os.getenv("FMP_API_KEY"))

    @staticmethod
    def fetch_data(endpoint: str) -> List[Dict[str, Any]]:
        """Fetch data from a specific FMP endpoint."""
        url = f"{FMPDataFetcher.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params={"apikey": FMPDataFetcher.API_KEY}, timeout=(5, 5))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching data from {endpoint}: {e}")
            return []

    @staticmethod
    def fetch_most_active_tickers() -> List[str]:
        """Fetch the most active tickers from FMP."""
        data = FMPDataFetcher.fetch_data("stock_market/actives")
        return [str(item['symbol']) for item in data if 'symbol' in item]

    @staticmethod
    def fetch_biggest_gainers() -> List[str]:
        """Fetch the biggest gainers from FMP."""
        data = FMPDataFetcher.fetch_data("stock_market/gainers")
        return [str(item['symbol']) for item in data if 'symbol' in item]

    @staticmethod
    def fetch_biggest_losers() -> List[str]:
        """Fetch the biggest losers from FMP."""
        data = FMPDataFetcher.fetch_data("stock_market/losers")
        return [str(item['symbol']) for item in data if 'symbol' in item]

    @staticmethod
    def fetch_additional_tickers() -> List[str]:
        """Fetch additional tickers to ensure minimum quantity."""
        data = FMPDataFetcher.fetch_data("nasdaq_constituent")
        return [str(item['symbol']) for item in data if 'symbol' in item]

class TickerScraper:
    MIN_TICKERS = 1000

    def __init__(self, constants: TCS):
        self.constants = constants
        self.fetched_tickers = [str(ticker) for ticker in self.load_fetched_tickers()]
        self.current_day = str(datetime.now().weekday())  # Monday is '0' and Sunday is '6'
        self.stock_screener = StockScreener()  # Initialize the StockScreener

    def load_fetched_tickers(self) -> List[str]:
        """Load fetched tickers from a JSON file if it exists."""
        if os.path.exists('fetched_tickers.json'):
            with open('fetched_tickers.json', 'r') as file:
                return [str(ticker) for ticker in json.load(file)]
        return []

    def save_fetched_tickers(self):
        """Save the fetched tickers to a JSON file."""
        with open('fetched_tickers.json', 'w') as file:
            json.dump(self.fetched_tickers, file)

    def reset_fetched_tickers(self):
        """Reset fetched tickers list and save."""
        self.fetched_tickers = []
        self.save_fetched_tickers()

    def get_active_tickers(self) -> List[str]:
        """Get the list of active tickers, ensuring at least 1000 unique tickers."""
        # Fetch tickers from the stock screener
        screener_tickers = [str(ticker) for ticker in self.stock_screener.fetch_stocks()]

        # Fetch tickers from various FMP endpoints
        active_tickers = FMPDataFetcher.fetch_most_active_tickers()
        gainers = FMPDataFetcher.fetch_biggest_gainers()
        losers = FMPDataFetcher.fetch_biggest_losers()

        # Combine all tickers and remove duplicates by converting to a set, then back to a list
        all_tickers = list(set(screener_tickers + active_tickers + gainers + losers))

        # Filter out already fetched tickers (assume `self.fetched_tickers` is a list of strings)
        new_tickers = [str(ticker) for ticker in all_tickers if ticker not in self.fetched_tickers]

        # Ensure there are at least 1000 unique tickers
        if len(new_tickers) < self.MIN_TICKERS:
            additional_tickers = FMPDataFetcher.fetch_additional_tickers()
            additional_needed = self.MIN_TICKERS - len(new_tickers)
            new_tickers.extend([str(ticker) for ticker in additional_tickers[:additional_needed]])

        # Update fetched tickers and save
        self.fetched_tickers.extend(new_tickers)
        self.fetched_tickers = list(set(self.fetched_tickers))  # Ensure uniqueness by using a set of strings (symbols)
        self.save_fetched_tickers()

        # Reset fetched tickers at the end of the trading week (e.g., Friday)
        if self.current_day == '4':  # Assuming Friday is '4'
            self.reset_fetched_tickers()

        return new_tickers[:self.MIN_TICKERS]

    def get_all_active_tickers(self) -> List[str]:
        """Return the list of all active tickers from FMP."""
        return self.get_active_tickers()

    def get_all_fetched_tickers(self) -> List[str]:
        """Return the list of all fetched tickers."""
        return self.fetched_tickers

def fetch_all_tickers() -> List[str]:
    """Fetch all tickers from FMP and return as a list."""
    ticker_scraper = TickerScraper(TCS())
    all_tickers = ticker_scraper.get_all_active_tickers()
    return all_tickers

def main():
    # Fetch all tickers using the TickerScraper
    all_tickers = fetch_all_tickers()
    
    # Print the fetched tickers
    print("Fetched tickers:", all_tickers)
    logging.info(f"Fetched tickers: {all_tickers}")

if __name__ == "__main__":
    main()