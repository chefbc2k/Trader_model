import requests
from typing import List, Dict, Any, DefaultDict
from collections import defaultdict
from dotenv import load_dotenv
import os
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Load environment variables
load_dotenv()

# Set up logging using LoggingMaster
logger = LoggingMaster("NewsGetter").get_logger()

class NewsGetter:
    def __init__(self, tickers: str, start_date: str, end_date: str):
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        self.news_base_url = "https://financialmodelingprep.com/api/v3/stock_news"
        self.news_limit = 5  # Set limit for news articles per request
        self.news_maximum = 30  # Set maximum number of news articles
        self.ticker = tickers
        self.start_date = start_date
        self.end_date = end_date

    def get_stock_news(self, page: int = 1) -> List[Dict[str, Any]]:
        """Fetches stock news from FMP API based on user inputs."""
        total_articles = []
        while len(total_articles) < self.news_maximum:
            endpoint = (
                f"{self.news_base_url}?tickers={self.ticker}"
                f"&page={page}"
                f"&from={self.start_date}"
                f"&to={self.end_date}"
                f"&limit={self.news_limit}"
                f"&apikey={self.fmp_api_key}"
            )

            try:
                response = requests.get(endpoint)
                response.raise_for_status()
                json_response = response.json()

                total_articles.extend(json_response)
                logger.info(f"Fetched {len(json_response)} articles for ticker: {self.ticker} (Total so far: {len(total_articles)})")
                
                if len(json_response) < self.news_limit or len(total_articles) >= self.news_maximum:
                    break  # Exit loop if no more articles are available or max limit is reached

                page += 1  # Move to the next page

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching stock news from FMP: {e}")
                break  # Exit on error

        return total_articles[:self.news_maximum]

    def compile_news(self, news_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Compiles news articles from fetched data for the specified ticker."""
        if not news_data:
            logger.warning(f"No news articles found for ticker {self.ticker}.")
            return defaultdict(list)  # Return an empty defaultdict to avoid errors

        combined_data: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)

        try:
            for news in news_data:
                if isinstance(news, dict):
                    key = news.get('symbol')
                    combined_data[key].append({
                        'symbol': news.get('symbol'),
                        'publishedDate': news.get('publishedDate'),
                        'title': news.get('title'),
                        'text': news.get('text') if news.get('text') else '',
                    })
        except TypeError as e:
            logger.error(f"Error processing news data for ticker {self.ticker}: {e}")
            return defaultdict(list)  # Return an empty defaultdict in case of an error

        # Log the total number of articles processed per ticker
        for ticker, articles in combined_data.items():
            logger.info(f"Ticker {ticker}: Processed {len(articles)} articles")

        return combined_data