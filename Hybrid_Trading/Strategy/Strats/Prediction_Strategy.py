import pandas as pd
import datetime
from sklearn.ensemble import GradientBoostingRegressor
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from typing import Dict, Any, List
from tqdm.asyncio import tqdm_asyncio
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.utils import TempFiles

class PredictionStrategy:
    def __init__(self, user_input: Any, logger=None):
        self.user_input = user_input
        self.temp_files = TempFiles()
        self.buy_signals = {}  
        self.logger = logger or LoggingMaster("PredictionStrategy").get_logger()

    def prepare_data(self, ticker: str, prophet_forecast: pd.DataFrame) -> pd.DataFrame:
        self.logger.info(f"Preparing data for {ticker}")
        print(f"Preparing data for {ticker}")

        df = pd.DataFrame(prophet_forecast)
        df['ds'] = pd.to_datetime(df['ds'])  

        # Handle missing values based on user input
        if self.user_input.get('handle_missing_values') == 'fill':
            fillna_method = self.user_input.get('fillna_method', 'mean')
            if fillna_method == 'mean':
                df.fillna(df.mean(), inplace=True)
            elif fillna_method == 'median':
                df.fillna(df.median(), inplace=True)
        elif self.user_input.get('handle_missing_values') == 'interpolate':
            df.interpolate(method='linear', inplace=True)
        elif self.user_input.get('handle_missing_values') == 'drop':
            df.dropna(inplace=True)
        
        return df

    def prepare_future_dataframe(self, df: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Preparing future dataframe with regressors")
        print("Preparing future dataframe with regressors")

        future['sentiment_score'] = df['sentiment_score'].iloc[-1]
        future['volume'] = df['volume'].iloc[-1]

        X = pd.DataFrame({'time': range(len(df))})
        y = df['bid_price'].values

        # Fit a gradient boosting model for bid price prediction
        linear_model = GradientBoostingRegressor()
        linear_model.fit(X, y)
        future_index = pd.DataFrame({'time': range(len(df), len(df) + len(future))})
        future['bid_price'] = linear_model.predict(future_index)

        # Apply exponential smoothing for ask price prediction
        exp_smoothing_model = SimpleExpSmoothing(df['ask_price']).fit()
        future['ask_price'] = exp_smoothing_model.forecast(len(future))

        return future

    async def process_ticker(self, ticker: str, ticker_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Processing ticker: {ticker}")

        # Extract relevant data
        prophet_forecast = pd.DataFrame(ticker_data.get("prophet_forecast", []))
        real_time_data = pd.DataFrame(ticker_data.get("real_time_data", []))

        if prophet_forecast.empty or real_time_data.empty:
            self.logger.error(f"Insufficient data available for {ticker}. Skipping strategy.")
            return None

        # Prepare the data
        df = self.prepare_data(ticker, prophet_forecast)

        self.logger.info(f"Using provided Prophet forecast for {ticker}")
        print(f"Using provided Prophet forecast for {ticker}")

        # Get predictions for today and 5 days out
        predicted_today = df[df['ds'] == str(datetime.date.today())]['yhat'].values[0]
        predicted_5_days_out = df[df['ds'] == str(datetime.date.today() + datetime.timedelta(days=5))]['yhat'].values[0]

        current_price = real_time_data['price'].iloc[-1]

        # Generate buy/hold signal based on conditions
        if abs(current_price - predicted_today) <= 0.01 * predicted_today:
            signal = {
                'action': 'buy',
                'reason': 'within 1% of today\'s predicted price',
                'ticker': ticker,
                'current_price': current_price,
                'predicted_today': predicted_today,
                'start_date': self.user_input.get('start_date'),
                'end_date': self.user_input.get('end_date')
            }
        elif current_price <= 0.98 * df['y'].iloc[-1] and predicted_5_days_out >= 1.03 * current_price:
            signal = {
                'action': 'buy',
                'reason': '2% below yesterday\'s close and predicted to rise by 3% in 5 days',
                'ticker': ticker,
                'current_price': current_price,
                'predicted_5_days_out': predicted_5_days_out,
                'start_date': self.user_input.get('start_date'),
                'end_date': self.user_input.get('end_date')
            }
        else:
            signal = {
                'action': 'hold',
                'reason': 'No buy signal',
                'ticker': ticker,
                'current_price': current_price,
                'start_date': self.user_input.get('start_date'),
                'end_date': self.user_input.get('end_date')
            }

        self.logger.info(f"Signal for {ticker}: {signal}")
        print(f"Signal for {ticker}: {signal}")

        # Store the buy signal
        self.buy_signals[ticker] = signal
        return signal

    async def run(self, tickers: List[str], fetched_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        self.logger.info("Running prediction strategy for tickers...")
        print("Running prediction strategy for tickers...")

        tasks = [self.process_ticker(ticker, fetched_data[ticker]) for ticker in tickers]
        results = {}

        # Process tickers asynchronously using tqdm for progress tracking
        async for task in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Processing Tickers", unit="ticker"):
            result = await task
            ticker = result.get('ticker')
            results[ticker] = result

        self.logger.info("Prediction strategy completed for all tickers.")
        print("Prediction strategy completed for all tickers.")
        return results

    def get_signals(self) -> Dict[str, Any]:
        return self.buy_signals