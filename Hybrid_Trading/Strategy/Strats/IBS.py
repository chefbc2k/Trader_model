import backtrader as bt
import pandas as pd
from datetime import timedelta
from asgiref.sync import sync_to_async
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from tqdm.asyncio import tqdm_asyncio
from Hybrid_Trading.Data.models import HistoricalPrice  # Only importing the necessary model for fetching data

class InstantBacktestStrategy(bt.Strategy):
    params = (
        ('stop_loss', 0.04),  # 4% stop loss
        ('take_profit', 0.02),  # 2% take profit
        ('ticker', None),  # Ticker symbol
        ('historical_data', None),  # Historical data passed to the strategy
        ('start_date', None),  # Start date for the backtest
        ('end_date', None),  # End date for the backtest
    )

    def __init__(self):
        self.order = None
        self.buy_price = None
        self.backtest_result = None  # To store the result of the instant backtest

    def next(self):
        if not self.position:
            if self.instant_backtest():
                self.order = self.buy()
                self.buy_price = self.data.close[0]
                self.backtest_result = {'signal': 'buy', 'price': self.buy_price}
                self.log(f"Buy order placed for {self.params.ticker} at {self.buy_price}")
        else:
            if self.data.close[0] <= self.buy_price * (1 - self.params.stop_loss):
                self.order = self.sell()
                self.backtest_result = {'signal': 'stop_loss', 'price': self.data.close[0]}
                self.log(f"Stop loss triggered for {self.params.ticker} at {self.data.close[0]}")
            elif self.data.close[0] >= self.buy_price * (1 + self.params.take_profit):
                self.order = self.sell()
                self.backtest_result = {'signal': 'take_profit', 'price': self.data.close[0]}
                self.log(f"Take profit triggered for {self.params.ticker} at {self.data.close[0]}")

    def instant_backtest(self):
        """
        Simulate the trade on the historical data for a specified date range.
        """
        historical_data = self.params.historical_data
        if historical_data is None or historical_data.empty:
            self.log(f"No historical data provided for {self.params.ticker}. Skipping backtest.")
            return False

        # Ensure the index is in datetime format
        if not pd.api.types.is_datetime64_any_dtype(historical_data.index):
            historical_data.index = pd.to_datetime(historical_data.index)

        # Filter data for the backtest range (start_date to end_date)
        filtered_data = historical_data[
            (historical_data.index >= self.params.start_date) & 
            (historical_data.index <= self.params.end_date)
        ]
        
        if filtered_data.empty:
            self.log(f"No data available in the specified date range for {self.params.ticker}.")
            return False

        self.log(f"Backtesting for {self.params.ticker} from {self.params.start_date} to {self.params.end_date}.")

        for i in range(1, len(filtered_data)):
            current_price = filtered_data.iloc[i]['close']
            previous_price = filtered_data.iloc[i - 1]['close']

            buy_threshold = previous_price * 0.98  # 2% downturn
            sell_threshold = previous_price * 1.05  # 5% upturn

            if current_price <= buy_threshold:
                self.log("Backtest passed: Buy signal")
                self.backtest_result = {'signal': 'buy', 'price': current_price}
                return True
            elif current_price >= sell_threshold:
                self.log("Backtest passed: Sell signal")
                self.backtest_result = {'signal': 'sell', 'price': current_price}
                return True

        self.log("Backtest failed: No favorable conditions")
        self.backtest_result = {'signal': 'hold', 'price': None}
        return False

    def log(self, txt):
        logger = LoggingMaster("InstantBacktestStrategy").get_logger()
        logger.info(txt)

async def run_backtest(ticker, historical_data, start_date, end_date):
    if not pd.api.types.is_datetime64_any_dtype(historical_data.index):
        historical_data.index = pd.to_datetime(historical_data.index)

    cerebro = bt.Cerebro()

    # Add strategy with the necessary parameters
    cerebro.addstrategy(
        InstantBacktestStrategy, 
        ticker=ticker, 
        historical_data=historical_data, 
        start_date=start_date, 
        end_date=end_date
    )

    # Convert the historical data to a backtrader feed
    data = bt.feeds.PandasData(dataname=historical_data)
    cerebro.adddata(data)

    # Set initial cash
    cerebro.broker.setcash(1000)

    # Run the backtest
    strategies = cerebro.run()

    if hasattr(strategies[0], 'backtest_result'):
        return strategies[0].backtest_result
    else:
        raise ValueError("The strategy did not generate a 'backtest_result'.")

class TradingStrategy:
    def __init__(self, user_input):
        self.logger = LoggingMaster("TradingStrategy").get_logger()
        self.user_input = user_input
        self.start_date = self.user_input.get('start_date')
        self.end_date = self.user_input.get('end_date')
        self.interval = self.user_input.get('interval')
        self.period = self.user_input.get('period')

    async def run(self, tickers):
        results = {}
        tasks = [self.instant_backtest(ticker) for ticker in tickers]

        async for task in tqdm_asyncio.as_completed(tasks, total=len(tickers), desc="Processing Tickers", unit="ticker"):
            result = await task
            ticker = result.get('ticker')
            results[ticker] = result

        return results

    async def instant_backtest(self, ticker: str) -> dict:
        # Fetch historical data from Django ORM
        historical_data = await sync_to_async(HistoricalPrice.objects.filter)(ticker=ticker)
        historical_data_df = pd.DataFrame(list(historical_data.values()))

        if historical_data_df.empty:
            self.logger.error(f"No historical data available for {ticker}. Skipping backtest.")
            return {"ticker": ticker, "signal": "no_data", "price": None}

        # Run the backtest asynchronously, passing start_date and end_date
        backtest_result = await run_backtest(ticker, historical_data_df, self.start_date, self.end_date)
        backtest_result['ticker'] = ticker
        return backtest_result