from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TCS:
    """Trading Constants and Settings"""
    def __init__(self):
        # Initialize PE_WEIGHTS before using it
        self.PE_WEIGHTS = {}

        # Define the scoring for analyst recommendations
        self.RECOMMENDATION_SCORES = {
            "StrongBuy": 5,
            "Buy": 4,
            "Hold": 2,
            "Sell": -1,
            "StrongSell": -2
        }

        # Example grading scores for estimate trends
        self.GRADE_SCORES = {
            "StrongBuy": 4,
            "Buy": 1,
            "Hold": 0,
            "Sell": -1,
            "StrongSell": -2
        }

        # Define the trend scoring
        self.TREND_SCORES = {
            "positive": 4,
            "neutral": 1,
            "negative": -1
        }

        # Define mapping for grading changes
        self.GRADE_CHANGE_SCORES = {
            ("Buy", "StrongBuy"): 2,
            ("Hold", "Buy"): 0.8,
            ("Sell", "Hold"): -0.5,
            ("StrongSell", "Sell"): -1,
            # Add more mappings as needed
        }

        # Backtesting and trading parameters
        self.POSITION_SIZE = 3
        self.QUANTITY = 10
        self.STARTING_ACCOUNT_VALUE = int(os.getenv("STARTING_ACCOUNT_VALUE", 1000))

        # Trading periods and intervals
        self.TRADING_PERIOD_MAPPING = {
            'short_term': '1m',
            'medium_term': '6m',
            'long_term': '1y',
        }

        self.TRADING_INTERVAL_MAPPING = {
            'short_term': '15min',
            'medium_term': '1h',
            'long_term': '1d',
        }

        # Logistic Regression Model Parameters
        self.LOGISTIC_REGRESSION_MODEL_PARAMETERS = {
            'max_iter': 200,
            'solver': 'lbfgs',
            'penalty': 'l2',
            'C': 1.0,
            'random_state': None
        }

        # Percentages of symbols to process
        self.PERCENTAGES = [1, 5, 10, 15, 25, 50, 75, 100]
        self.DEFAULT_PERCENTAGE = 10

        # General Trading Parameters
        self.COMMISSION_RATE = 0.002
        self.MAX_STOP_LOSS_PERCENT = float(os.getenv("MAX_STOP_LOSS_PERCENT", 0.05))
        self.LONG_TERM_PROFIT_TARGET = float(os.getenv("LONG_TERM_PROFIT_TARGET", 0.20))
        self.LONG_TERM_STOP_LOSS_PERCENT = float(os.getenv("LONG_TERM_STOP_LOSS_PERCENT", 0.10))
        self.BATCH_SIZE = 100
        self.NUMBER_OF_BATCHES = 50
        self.MAX_WORKERS = min(50, os.cpu_count())  # Example, capped at 32
        self.MAX_INVESTMENT_PARTITION = 0.1
        self.TRADING_STRATEGY_THREAD_COUNT = 65

        # Define all trading periods from FMP
        self.TRADING_PERIODS = [
            '1m',   # 1 month
            '3m',   # 3 months
            '6m',   # 6 months
            '1y',   # 1 year
            '5y',   # 5 years
            '10y',  # 10 years
            'ytd'   # Year-to-date
        ]

        # Define all trading intervals from FMP
        self.TRADING_INTERVALS = [
            '1min',  # 1 minute
            '5min',  # 5 minutes
            '15min', # 15 minutes
            '30min', # 30 minutes
            '1h',    # 1 hour
            '4h',    # 4 hours
            '1d',    # 1 day
            '1wk',   # 1 week
            '1mo'    # 1 month
        ]

        # Miscellaneous Parameters
        self.BLACKLIST = ['BTC-USD', '^N225',]
        self.STOCK_MARKET_OPEN_TIME = os.getenv("STOCK_MARKET_OPEN_TIME", "05:00")
        self.STOCK_MARKET_CLOSE_TIME = os.getenv("STOCK_MARKET_CLOSE_TIME", "16:00")
        self.STOCKS_TO_CHECK = os.getenv("STOCKS_TO_CHECK", "AAPL,INTC,AMD,NVDA,TSLA,META,...").split(",")
        self.ARTICLE_MIN_COUNT_NEWS = int(os.getenv("ARTICLE_MIN_COUNT_NEWS", 7))
        self.ANALYSIS_INTERVAL = int(os.getenv("ANALYSIS_INTERVAL", 60))
        self.STOCK_SCANNER_PARTITION_COUNT = int(os.getenv("STOCK_SCANNER_PARTITION_COUNT", 10))

        # Trading Modes
        self.MODES = {
            "infinite_day_trading": "Infinite Day Trading",
            "period_day_trading": "Period Day Trading"
        }

        # FMP Intervals for Backtesting or Testing
        self.FMP_INTERVALS = ['daily', 'weekly', 'monthly']

        # Parameter Ranges
        self.SHORT_WINDOW_RANGE = range(5, 201)
        self.LONG_WINDOW_RANGE = range(20, 401)
        self.FAST_WINDOW_RANGE = range(2, 51)
        self.SLOW_PERIOD_RANGE = range(10, 101)
        self.SIGNAL_PERIOD_RANGE = range(1, 21)
        self.PERIOD_RANGE = range(3, 51)

        # Weights for Technical Indicators
        self.TIWEIGHTS = {
            "sma": 0.1,
            "ema": 0.1,
            "wma": 0.2,
            "dema": 0.1,
            "tema": 0.2,
            "williams": 0.4,
            "rsi": 0.4,
            "adx": 0.5,
            "standardDeviation": 0.15
        }

        # Thresholds for indicators
        self.TITHRESHOLDS = {
            "sma": {"buy": 25, "sell": 75},
            "ema": {"buy": 25, "sell": 75},
            "wma": {"buy": 25, "sell": 75},
            "dema": {"buy": 25, "sell": 75},
            "tema": {"buy": 25, "sell": 75},
            "williams": {"buy": -90, "sell": -10},
            "rsi": {"buy": 25, "sell": 75},
            "adx": {"buy": 20, "sell": 15},
            "standardDeviation": {"buy": 0.05, "sell": 0.20}
        }

        # Define weights for score calculation on a scale of 1-10
        self.PE_WEIGHTS.update({
            'pe_ratio': 8,
            'volume_avg': 5,
            'price_to_book': 7,
            'dividend_yield': 6,
            'market_cap': 6,
            'price_to_sales': 6,
            'debt_to_equity': 7,
            'current_ratio': 7,
            'quick_ratio': 7,
            'cash_flow_per_share': 8,
            'sharpe_ratio': 9,
        })

        # Expanded stock metrics functions
        self.STOCK_METRICS = {
            'pe_ratio': lambda data: data['Close'].mean() / data['EPS'].mean() if 'EPS' in data else 0,
            'volume_avg': lambda data: data['Volume'].mean() if 'Volume' in data else 0,
            'price_to_book': lambda data: data['Close'].mean() / data['Book Value Per Share'].mean() if 'Book Value Per Share' in data else 0,
            'dividend_yield': lambda data: data['Dividends'].sum() / data['Close'].mean() if 'Dividends' in data else 0,
            'market_cap': lambda data: data['Shares Outstanding'].mean() * data['Close'].mean() if 'Shares Outstanding' in data else 0,
            'price_to_sales': lambda data: data['Close'].mean() if 'Revenue Per Share' in data else 0,
            'debt_to_equity': lambda data: data['Total Debt'].mean() / data['Shareholders Equity'].mean() if 'Total Debt' in data and 'Shareholders Equity' in data else 0,
            'current_ratio': lambda data: data['Current Assets'].mean() / data['Current Liabilities'].mean() if 'Current Assets' in data and 'Current Liabilities' in data else 0,
                        'quick_ratio': lambda data: (data['Current Assets'].mean() - data['Inventory'].mean()) / data['Current Liabilities'].mean() if 'Current Assets' in data and 'Inventory' in data and 'Current Liabilities' in data else 0,
            'cash_flow_per_share': lambda data: data['Operating Cash Flow'].mean() / data['Shares Outstanding'].mean() if 'Operating Cash Flow' in data and 'Shares Outstanding' in data else 0,
            'sharpe_ratio': lambda data: (data['Returns'].mean() - 0.01) / data['Returns'].std() if 'Returns' in data else 0,  # Risk-free rate assumed at 0.01
        }

        # Criteria for a good stock based on score
        self.GOOD_STOCK_SCORE_THRESHOLD = 5.0  # Example threshold
        self.GOOD_STOCK_RANK_THRESHOLD = 10  # Example threshold
        self.GOOD_STOCK_TRADE_COUNT_THRESHOLD = 10  # Example threshold
        self.BAD_STOCK_SCORE_THRESHOLD = 0.1  # Example threshold

        # Grading Criteria for Stock Insights
        self.GRADE_SCORES.update({
            ("Outperform", "Outperform"): 4.0,
            ("Outperform", "Underperform"): 2.0,
            ("Underperform", "Outperform"): 3.0,
            ("Neutral", "Neutral"): 1.0,
            "Strong Buy": 5,
            "Buy": 4,
            "Hold": 3,
            "Sell": 2,
            "Strong Sell": 1,
            "Outperform": 1.5,
            "Underperform": 2.5
        })

        # Grading Criteria for Stock State
        self.STOCK_GRADES = {
            "A": 8.0,
            "B": 6.0,
            "C": 4.0,
            "D": 2.0
        }

        # Example Trading Strategy Parameters
        self.TRIX_PERIOD = 15
        self.TRIX_THRESHOLD = 0.1
        self.AROON_PERIOD = 25
        self.AROON_UP_THRESHOLD = 50
        self.AROON_DOWN_THRESHOLD = 49
        self.ELDER_RAY_BULL_THRESHOLD = 0.0
        self.ELDER_RAY_BEAR_THRESHOLD = 0.1

        # Risk Management Parameters
        self.POSITION_SIZE = 0.02  # Percentage of portfolio to risk on a single trade
        self.MAX_RISK_PER_TRADE = 0.01  # Maximum risk per trade as a percentage of the portfolio

        # Logging and Debugging
        self.LOG_LEVEL = logging.INFO  # Logging level
        self.LOG_FILE = 'trading_log.log'  # Log file name

        # Notification Settings
        self.ENABLE_NOTIFICATIONS = True  # Enable notifications
        self.NOTIFICATION_EMAIL = 'chebc2k@me.com'  # Email address for notifications
        self.NOTIFICATION_THRESHOLD = 0.05  # Threshold for sending notifications (e.g., price change)

        # Time Settings
        self.MARKET_OPEN_TIME = '09:30'  # Market open time
        self.MARKET_CLOSE_TIME = '16:00'  # Market close time
        self.TRADING_SESSION_DURATION = '6h30m'  # Duration of the trading session
        self.TIMEZONE = 'US/Eastern'  # Timezone for market times

        # Expanded Performance Metrics
        self.PERFORMANCE_METRICS = {
            "sharpe_ratio": 0.1,
            "sortino_ratio": 0.2,
            "calmar_ratio": 0.2,
            "max_drawdown": 0.1,
            "annual_return": 0.4,
            "volatility": 0.05,
            "alpha": 0.025,
            "beta": 0.025
        }

        # Indicators
        self.INDICATORS = {
            "sma": {},
            "ema": {},
            "wma": {},
            "dema": {},
            "tema": {},
            "williams": {},
            "rsi": {},
            "adx": {},
            "standardDeviation": {}
        }

        # Sentiment Priorities
        # Bullish Words Priority
        self.BULLISH_HIGH_PRIORITY = (0.83, 1.0)
        self.BULLISH_MEDIUM_PRIORITY = (0.67, 0.82)
        self.BULLISH_LOW_PRIORITY = (0.5, 0.66)

        # Neutral Words Priority
        self.NEUTRAL_HIGH_PRIORITY = -0.1
        self.NEUTRAL_MEDIUM_PRIORITY = -0.05
        self.NEUTRAL_LOW_PRIORITY = 0.0

        # Earnings Words Priority
        self.EARNINGS_HIGH_PRIORITY = (0.63, 0.7)
        self.EARNINGS_MEDIUM_PRIORITY = (0.57, 0.62)
        self.EARNINGS_LOW_PRIORITY = (0.5, 0.56)

        # Bearish Words Priority
        self.BEARISH_HIGH_PRIORITY = (-1.5, -1.17)
        self.BEARISH_MEDIUM_PRIORITY = (-1.16, -0.83)
        self.BEARISH_LOW_PRIORITY = (-0.82, -0.5)

        # Default sentiment values
        self.DEFAULT_SENTIMENT_VALUES = {
            "bullish": 0.42,
            "neutral": 0.0,
            "bearish": -0.48
        }

        self.TECHNICAL_INDICATOR_PERIODS = {
            "sma": 10,            # Shorter period for faster response
            "ema": 8,             # Shorter period for quicker trend identification
            "wma": 5,             # Very short to catch the earliest signs
            "dema": 10,           # Shorter for more aggressive trading
            "tema": 20,           # Shorter but slightly longer than DEMA for confirmation
            "williams": 7,        # Shorter period to increase sensitivity
            "rsi": 14,            # Standard period, but sensitive enough
            "adx": 10,            # Shorter period for quick trend strength detection
            "standardDeviation": 10  # Shorter to detect volatility quickly
        }

        self.TECHNICAL_INDICATOR_INTERVALS = {
            "sma": "1min",       # Very short to act on immediate trends
            "ema": "5min",        # Quick intervals to catch early movements
            "wma": "5min",        # Matching quick response time
            "dema": "5min",       # Slightly longer but still aggressive
            "tema": "15min",      # Provides some confirmation but remains fast
            "williams": "5min",   # Short interval to increase reaction time
            "rsi": "5min",        # Still relatively short for quick decisions
            "adx": "10min",       # Slightly longer to measure trend strength adequately
            "standardDeviation": "1min"  # To capture rapid changes in volatility
        }

        # Generate the endpoint URL for technical indicators
        self.MINFMPBASE_URL = "https://financialmodelingprep.com/api/v3/technical_indicator/"

    def get_indicator_url(self, ticker: str, indicator: str) -> str:
        """
        Returns the URL for the specified indicator, ticker, and period.
        """
        endpoint = f"{self.MINFMPBASE_URL}{self.TECHNICAL_INDICATOR_INTERVALS[indicator]}/{ticker}?type={indicator}&period={self.TECHNICAL_INDICATOR_PERIODS[indicator]}"
        return endpoint