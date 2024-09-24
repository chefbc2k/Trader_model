import asyncio
import pandas as pd
from datetime import datetime
import backtrader as bt
from typing import Dict, Any, List
from Config.trading_constants import TCS
from Config.utils import TempFiles
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Hybrid_Trading.Strategy.Strats.Dynamic_Strategy import DynamicStrategy
from Hybrid_Trading.Strategy.Strats.Prediction_Strategy import PredictionStrategy
from Hybrid_Trading.Strategy.Strats.IBS import InstantBacktestStrategy
from Hybrid_Trading.Strategy.Strats.MRMS import MeanReversionMomentumStrategy
from Hybrid_Trading.Strategy.Strats.VRS import VolatilityReversionStrategy
from Hybrid_Trading.Strategy.Strats.VS import ValueSeekerStrategy
from Hybrid_Trading.Trading.TL.Trading_Logic import DayTradingLogic
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio  # Async-friendly TQDM progress bar
from Hybrid_Trading.Data.models import HistoricalData
from Hybrid_Trading.Symbols.models import Tickers
from Hybrid_Trading.Backtester.models import BacktestResults, BacktestResultsTradeLogs
from django.utils import timezone

# Load environment variables
load_dotenv()

class PandasData(bt.feeds.PandasData):
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )

class DayTradingBacktester:
    def __init__(self, user_input: Dict[str, Any], filepath: str):
        self.logger = LoggingMaster("DayTradingBacktester").get_logger()
        self.logger.info("Initializing DayTradingBacktester...")
        
        self.user_input = user_input
        self.constants = TCS()
        self.STARTING_ACCOUNT_VALUE = self.constants.STARTING_ACCOUNT_VALUE
        self.cash = self.STARTING_ACCOUNT_VALUE
        self.portfolio: Dict[str, int] = {}
        self.trade_log: List[Dict[str, Any]] = []

        self.filepath = TempFiles().get_path('backtest_results')

        # Initialize DayTradingLogic for executing trades
        self.day_trading_logic = DayTradingLogic(user_input=self.user_input)

        self.logger.info(f"Initialized with starting account value: {self.STARTING_ACCOUNT_VALUE}")

    async def pull_historical_data(self, ticker: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """
        Async fetch historical data for a given ticker using Django ORM.
        """
        self.logger.info(f"Fetching historical data for ticker: {ticker}")
        try:
            ticker_instance = await Tickers.objects.aget(ticker=ticker)  # Async ORM call
            historical_data_qs = HistoricalData.objects.filter(ticker=ticker_instance).order_by('date')

            if start_date and end_date:
                historical_data_qs = historical_data_qs.filter(date__range=[start_date, end_date])

            historical_data_df = pd.DataFrame(list(await historical_data_qs.values(  # Async ORM query
                'date', 'open', 'high', 'low', 'close', 'volume'
            )))
            historical_data_df.set_index('date', inplace=True)

            self.logger.info(f"Fetched {len(historical_data_df)} rows of data for {ticker}")
            return historical_data_df

        except Tickers.DoesNotExist:
            self.logger.error(f"Ticker {ticker} does not exist in the database.")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
            return pd.DataFrame()

    async def execute_backtest(self, historical_data: pd.DataFrame, ticker: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute backtest asynchronously for a given ticker using the aggregated signals.
        """
        self.logger.info(f"Executing backtest for {ticker}")
        
        for date in historical_data.index:
            signal = signals.get(date, {})
            if not signal:
                continue

            trade_log = await self.day_trading_logic.execute_trade(ticker, signal)  # Async trade execution

            if trade_log:
                self.trade_log.append(trade_log)

        portfolio_value = self.cash + sum(self.portfolio[t] * historical_data.at[date, 'close'] for t in self.portfolio)
        return {
            'ticker': ticker,
            'final_portfolio_value': portfolio_value,
            'trade_log': self.trade_log
        }

    async def aggregate_signals(self, strategy_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate signals asynchronously from different strategies using majority vote.
        """
        self.logger.info("Aggregating signals using majority vote...")

        combined_signals = {}
        for signals in strategy_signals:
            for date, signal in signals.items():
                if date not in combined_signals:
                    combined_signals[date] = {'Buy': 0, 'Sell': 0}
                if signal.get('final_action') == 'Buy':
                    combined_signals[date]['Buy'] += 1
                elif signal.get('final_action') == 'Sell':
                    combined_signals[date]['Sell'] += 1

        final_signals = {}
        for date, vote_counts in combined_signals.items():
            final_signals[date] = {
                'final_action': 'Buy' if vote_counts['Buy'] > vote_counts['Sell'] else 'Sell'
            }
        return final_signals

    async def run(self, fetched_data: List[Dict[str, Any]], start_date: datetime = None, end_date: datetime = None):
        """
        Run backtest asynchronously for all tickers in the fetched data list.
        """
        self.logger.info("Starting backtesting process...")
        backtest_results = []

        tasks = []
        for data in fetched_data:
            ticker = data.get('ticker')

            task = asyncio.create_task(self.process_ticker(ticker, start_date, end_date))  # Schedule async task
            tasks.append(task)

        for task in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Backtesting Tickers"):  # TQDM for async
            result = await task
            backtest_results.append(result)

        await self.export_results(backtest_results)
        self.logger.info("Backtesting process completed and results exported.")

    async def process_ticker(self, ticker: str, start_date: datetime, end_date: datetime):
        """
        Process a single ticker asynchronously.
        """
        # Fetch historical data using ORM with date range filtering
        historical_data = await self.pull_historical_data(ticker, start_date, end_date)

        strategies = [
            DynamicStrategy(historical_data),
            PredictionStrategy(historical_data),
            InstantBacktestStrategy(historical_data),
            MeanReversionMomentumStrategy(historical_data),
            VolatilityReversionStrategy(historical_data),
            ValueSeekerStrategy(historical_data)
        ]

        signals = [strategy.generate_signals() for strategy in strategies]
        aggregated_signals = await self.aggregate_signals(signals)
        result = await self.execute_backtest(historical_data, ticker, aggregated_signals)
        return result

    async def export_results(self, results: List[Dict[str, Any]]):
        """
        Save backtesting results asynchronously to the database.
        """
        try:
            for result in results:
                ticker_symbol = result.get('ticker')
                final_portfolio_value = result.get('final_portfolio_value')
                trade_logs = result.get('trade_log')

                try:
                    ticker = await Tickers.objects.aget(ticker=ticker_symbol)  # Async ORM fetch
                except Tickers.DoesNotExist:
                    self.logger.error(f"Ticker {ticker_symbol} does not exist in the database.")
                    continue

                backtest_result = await BacktestResults.objects.acreate(  # Async ORM create
                    ticker=ticker,
                    final_portfolio_value=final_portfolio_value,
                    trade_log=trade_logs,
                    backtest_date=timezone.now()
                )

                self.logger.info(f"Saved backtest result for {ticker_symbol} with final portfolio value: {final_portfolio_value}")

                for trade_log in trade_logs:
                    await BacktestResultsTradeLogs.objects.acreate(  # Async ORM create
                        ticker=ticker,
                        action=trade_log.get('action'),
                        quantity=trade_log.get('quantity'),
                        price=trade_log.get('price'),
                        date=trade_log.get('date'),
                        portfolio_value=trade_log.get('current_portfolio_value')
                    )
                    self.logger.info(f"Logged trade: {trade_log['action']} on {trade_log['date']} for {ticker_symbol}")

        except Exception as e:
            self.logger.error(f"Failed to save backtest results to the database: {e}")