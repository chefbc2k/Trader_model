from cgitb import reset
from collections import defaultdict
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # Replace alive_bar with tqdm for consistency
from dotenv import load_dotenv
from Hybrid_Trading.Data.Storage.CDS import CentralizedDataStorage
from Hybrid_Trading.Inputs.user_input import UserInput  # Import UserInput
import Config.trading_constants as constants
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.  utils import TradingDataWorkbook
from typing import DefaultDict, List, Dict, Any, Tuple
import numpy as np
from statistics import mean
from dateutil import parser

load_dotenv()
# Initialize the logger once for the session
logger = LoggingMaster("NewsClassifier").get_logger()
# Financial word classification
financial_word_classification = {
        # Bullish words
    "bullish": 2.0, "rally": 0.8, "growth": 0.5, "buy": 0.6, "gain": 0.6,
    "surge": 0.8, "uptrend": 0.9, "strong": 0.6, "positive": 0.6, "optimistic": 0.8,
    "increase": 0.7, "rise": 0.7, "improve": 0.6, "expand": 0.6, "advancing": 0.8,
    "booming": 0.9, "benefit": 0.6, "prosperous": 0.8, "thriving": 0.9, "escalate": 0.6,
    "growing": 0.6, "appreciate": 0.8, "bull market": 1.0, "bull": 1.0, "elevate": 0.6,
    "outperform": 0.7, "upside": 0.8, "record high": 2.0, "exceed": 0.8, "profit": 0.7,
    "rebound": 0.7, "soar": 1.0, "strengthen": 0.7, "revive": 0.7, "expand": 0.7,
    "impressive": 0.6, "capitalize": 0.7, "maximize": 0.6, "accelerate": 0.8, "resilient": 0.6,
    "gain momentum": 0.9, "outpace": 0.8, "peak": 0.8, "achieve": 0.7, "advance": 0.7,
    
    # Neutral words
    "steady": 0.0, "neutral": 0.0, "flat": 0.0, "stable": 0.0, "unchanged": 0.0,
    "consistent": 0.0, "balanced": 0.0, "even": 0.0, "moderate": 0.0, "sideways": -0.1,
    "average": 0.0, "regular": 0.0, "fixed": 0.0, "uniform": 0.0, "unbiased": 0.0,
    "medium": 0.0, "level": 0.0, "static": 0.0, "midpoint": 0.0, "normal": 0.0,
    "settled": 0.0, "status quo": 0.0, "ordinary": 0.0, "typical": 0.0, "unvaried": 0.0,
    "equilibrium": 0.0, "constant": 0.0, "routine": 0.0, "median": 0.0, "non-volatile": 0.0,

   # Earnings related words
    "earnings": 0.6, "profit": 0.7, "revenue": 0.6, "income": 0.5, "dividends": 0.6,
    "gross": 0.5, "net": 0.5, "sales": 0.5, "turnover": 0.5, "yield": 0.5,
    "proceeds": 0.5, "gains": 0.6, "returns": 0.6, "cash flow": 0.5, "earnings per share": 0.6,
    "profits": 0.7, "surplus": 0.6, "margin": 0.5, "benefits": 0.6, "financials": 0.5,
    "capital": 0.5, "revenue growth": 0.7, "profit margins": 0.6, "net income": 0.6, "operating income": 0.6,
    "retained earnings": 0.6, "gross income": 0.5, "net profit": 0.7, "profitability": 0.7, "dividend yield": 0.6,
    "operating margin": 0.6, "earnings growth": 0.7, "earnings report": 0.5, "quarterly earnings": 0.6, "revenue stream": 0.6,
    "top line": 0.5, "bottom line": 0.6, "earnings call": 0.5, "income statement": 0.5, "pre-tax income": 0.6,
    "EBITDA": 0.7, "operating profit": 0.6, "financial performance": 0.5, "revenue projection": 0.6, "dividend payout": 0.6,

    # Bearish words
    "bearish": -1.5, "fell": -0.5, "sell": -0.7, "decline": -0.7, "drop": -0.8,
    "downtrend": -0.9, "weak": -0.6, "negative": -0.5, "pessimistic": -0.7, "loss": -0.8,
    "decrease": -0.6, "fall": -0.5, "reduce": -0.6, "shrink": -0.6, "slump": -0.8,
    "plummet": -1.0, "diminish": -0.6, "bear market": -1.5, "bear": -1.0, "sell-off": -0.8,
    "underperform": -0.7, "downside": -0.9, "record low": -1.0, "weaken": -0.6, "declining": -0.7, "downward": -0.6,
    "deficit": -0.8, "negative growth": -0.7, "underwhelming": -0.5, "crash": -1.0,
}

# Initialize the sentiment analyzer and update its lexicon
sentiment_polarity_analyzer = SentimentIntensityAnalyzer()
sentiment_polarity_analyzer.lexicon.update(financial_word_classification)


class NewsClassifier:
    def __init__(self, user_input: Dict[str, Any], ticker: str, start_date: str, end_date: str, period: str, interval: str, storage: CentralizedDataStorage):
        self.user_input = user_input
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.interval = interval
        self.storage = storage  # Centralized storage

        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.sentiment_analyzer.lexicon.update(financial_word_classification)
        self.tcs = constants.TCS()

        self.workbook = TradingDataWorkbook(self.ticker)
        self.logger = logger  # Use the session-wide logger
        self.logger.info(f"Initialized NewsClassifier for ticker {self.ticker} with user input")

        # Dynamic thresholds and keyword tracking
        self.sentiment_history = []
        self.keyword_frequencies = defaultdict(int)

    def classify_news(self, news_data: DefaultDict[str, List[Dict[str, Any]]], max_workers: int = 15) -> DefaultDict[str, List[Dict[str, Any]]]:
        classified_news = defaultdict(list)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_article, ticker, article): article
                for ticker, articles in news_data.items()
                for article in articles[:30]  # Cap at 30 articles per ticker
            }
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Classifying news articles", unit="article"):
                result = future.result()
                if result:
                    ticker, processed_article = result
                    classified_news[ticker].append(processed_article)

        self.logger.info("Classified news articles")
        return classified_news

    def process_article(self, ticker: str, article: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        text = article.get('text', '')
        title = article.get('title', '')
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)

        # Print the sentiment score for monitoring
        print(f"Sentiment score for article: {sentiment_scores['compound']}")
        self.logger.info(f"Sentiment score for article: {sentiment_scores['compound']}")

        # Use calculate_dynamic_thresholds to determine thresholds
        threshold_positive, threshold_negative = self.calculate_dynamic_thresholds()

        # Handle sentiment assignment based on calculated dynamic thresholds
        sentiment = {'classification': 'neutral'}
        if sentiment_scores['compound'] >= threshold_positive:
            sentiment = {'classification': 'positive'}
        elif sentiment_scores['compound'] <= threshold_negative:
            sentiment = {'classification': 'negative'}

        keywords = self.extract_keywords(title, text)
        self.update_keyword_frequencies(keywords)
        published_date = article.get('publishedDate')

        recency_weight = self.calculate_recency_weight(published_date)
        weighted_sentiment = sentiment_scores['compound'] * recency_weight
        self.sentiment_history.append(weighted_sentiment)

        processed_article = {
            'symbol': ticker,
            'publishedDate': published_date,
            'title': title,
            'text': text,
            'url': article.get('url'),
            'site': article.get('site'),
            'sentiment': sentiment,
            'sentimentScores': sentiment_scores,
            'weightedSentiment': weighted_sentiment,
            'keywords': keywords
        }
        return ticker, processed_article

    def calculate_dynamic_thresholds(self, std_multiplier: float = 1.5) -> Tuple[float, float]:
        """Calculate dynamic sentiment thresholds based on historical sentiment data."""
        if not self.sentiment_history:
            self.logger.warning("Sentiment history is empty. Applying default thresholds.")
            tcs = constants.TCS()  # Initialize the TCS class to access thresholds
            return tcs.DEFAULT_SENTIMENT_VALUES.get("bullish", 0.6), tcs.DEFAULT_SENTIMENT_VALUES.get("bearish", -0.6)

        assert all(isinstance(x, (int, float)) for x in self.sentiment_history), "All items in sentiment_history should be numeric"

        mean_sentiment = mean(self.sentiment_history)
        std_sentiment = np.std(self.sentiment_history)

        threshold_positive = mean_sentiment + (std_sentiment * std_multiplier)
        threshold_negative = mean_sentiment - (std_sentiment * std_multiplier)

        return threshold_positive, threshold_negative

    def calculate_recency_weight(self, published_date: str) -> float:
        try:
            parsed_date = parser.parse(published_date)
            if parsed_date.tzinfo is not reset:
                parsed_date = parsed_date.replace(tzinfo=None)
        except (ValueError, OverflowError) as e:
            self.logger.error(f"Failed to parse date '{published_date}': {e}. Using current date as fallback.")
            parsed_date = datetime.now()

        days_ago = (datetime.now() - parsed_date).days
        return max(0.1, 1 - (days_ago / 365))

    def extract_keywords(self, title: str, text: str) -> List[str]:
        combined_content = f"{title} {text}"
        words = combined_content.split()
        keywords = [word for word in words if word.lower() in financial_word_classification]
        return keywords

    def update_keyword_frequencies(self, keywords: List[str]):
        for keyword in keywords:
            self.keyword_frequencies[keyword] += 1

    def calculate_stock_scores(self, classified_news: DefaultDict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        stock_scores = {}
        keyword_tracking = {}
        signal_counts = {'buy': 0, 'sell': 0, 'hold': 0}

        self.logger.debug(f"classified_news: {classified_news}")

        for ticker, articles in classified_news.items():
            if not isinstance(articles, list):
                self.logger.error(f"Unexpected data structure in NC for ticker {ticker}: {articles}")
                continue

            if ticker not in stock_scores:
                stock_scores[ticker] = {'score': 0, 'articles': 0, 'keywords': [], 'news_final_signal': 'hold'}

            for news in articles:
                if not isinstance(news, dict):
                    self.logger.error(f"Unexpected data structure for news-in-NC: {news}")
                    continue

                sentiment_score = news.get('sentimentScores', {}).get('compound', 0)
                keywords = news.get('keywords', [])

                stock_scores[ticker]['score'] += sentiment_score
                stock_scores[ticker]['articles'] += 1
                stock_scores[ticker]['keywords'].extend(keywords)

            if stock_scores[ticker]['articles'] < 30:
                weight_factor = 30 / stock_scores[ticker]['articles']
                stock_scores[ticker]['score'] *= weight_factor

            if stock_scores[ticker]['articles'] > 0:
                stock_scores[ticker]['average_score'] = stock_scores[ticker]['score'] / stock_scores[ticker]['articles']
            else:
                stock_scores[ticker]['average_score'] = 0

            if stock_scores[ticker]['average_score'] > 0.04:
                signal_counts['buy'] += 1
            elif stock_scores[ticker]['average_score'] < -0.03:
                signal_counts['sell'] += 1
            else:
                signal_counts['hold'] += 1

            max_count = max(signal_counts.values())
            tie_signals = [signal for signal, count in signal_counts.items() if count == max_count]

            if len(tie_signals) == 1:
                stock_scores[ticker]['news_final_signal'] = {'signal': tie_signals[0]}
            else:
                stock_scores[ticker]['news_final_signal'] = {'signal': 'hold'}

            keyword_tracking[ticker] = list(set(stock_scores[ticker]['keywords']))

        self.workbook.save_to_sheet(pd.DataFrame(stock_scores).T, "Stock Scores")
        self.logger.info("Calculated and saved stock scores for tickers")

        return {
            'stock_scores': stock_scores,
            'keyword_tracking': keyword_tracking,
            'signal_counts': signal_counts
        }

    def save_classified_news(self, classified_news: DefaultDict[str, List[Dict[str, Any]]]):
        news_data = []
        for ticker, articles in classified_news.items():
            for article in articles:
                news_data.append({
                    'Ticker': ticker,
                    'Published Date': article.get('publishedDate'),
                    'Title': article.get('title'),
                                        'Text': article.get('text'),
                    'URL': article.get('url'),
                    'Site': article.get('site'),
                    'Sentiment': article.get('sentiment').get('classification'),
                    'Sentiment Score': article.get('sentimentScores').get('compound'),
                    'Weighted Sentiment': article.get('weightedSentiment'),
                    'Keywords': ', '.join(article.get('keywords', []))
                })
        
        df_news = pd.DataFrame(news_data)
        self.workbook.save_to_sheet(df_news, "Classified News")
        self.logger.info("Saved classified news articles to workbook")

    def update_sentiment_history(self, sentiment_score: float):
        """Update the sentiment history with a new score."""
        self.sentiment_history.append(sentiment_score)
        if len(self.sentiment_history) > 100:  # Maintain a rolling history of the last 100 sentiment scores
            self.sentiment_history.pop(0)

    def summarize_classification(self, stock_scores: Dict[str, Any]):
        """Create a summary of the classification results."""
        summary_data = []
        for ticker, scores in stock_scores['stock_scores'].items():
            summary_data.append({
                'Ticker': ticker,
                'Average Sentiment Score': scores.get('average_score', 0),
                'Number of Articles': scores.get('articles', 0),
                'Final Signal': scores.get('news_final_signal', {}).get('signal', 'hold')
            })
        
        df_summary = pd.DataFrame(summary_data)
        self.workbook.save_to_sheet(df_summary, "Classification Summary")
        self.logger.info("Saved classification summary to workbook")

    def run_news_classification(self):
        """Main method to run the news classification process."""
        self.logger.info(f"Starting news classification for ticker {self.ticker}...")
        
        # Step 1: Retrieve the news data from centralized storage
        news_data = self.storage.retrieve(self.ticker, "news_articles")
        if not news_data:
            self.logger.error(f"No news data found for {self.ticker}")
            return
        
        # Step 2: Classify the news
        classified_news = self.classify_news(news_data)
        
        # Step 3: Calculate stock scores
        stock_scores = self.calculate_stock_scores(classified_news)
        
        # Step 4: Save the classified news and summary
        self.save_classified_news(classified_news)
        self.summarize_classification(stock_scores)

        self.logger.info(f"Completed news classification for ticker {self.ticker}")