import os
import threading
from typing import Dict, Tuple
import pandas as pd
import xgboost as xgb
from darts import TimeSeries
from darts.models import ARIMA, ExponentialSmoothing, Theta, RNNModel
from darts.utils.missing_values import fill_missing_values
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from lime.lime_tabular import LimeTabularExplainer
import shap
from bokeh.plotting import figure, save
from bokeh.models import HoverTool
from datetime import datetime, timedelta
from plyer import notification
from dotenv import load_dotenv
import holidays
from Hybrid_Trading.Model_Trainer.Self_Teaching import SelfTeaching
from Hybrid_Trading.Data.Storage.CDS import CentralizedDataStorage
from Hybrid_Trading.Log.Logging_Master import LoggingMaster  # Import LoggingMaster for consistent logging
# Load environment variables
load_dotenv()

class TimeSeriesForecaster:
    def __init__(self, user_input, ticker: str, interval: str, start_date: str, end_date: str, period: str,
                 base_dir: str = "forecasts", prediction_horizon: int = 5, fill_na_method: str = 'mean'):
        self.ticker = ticker
        self.user_input = user_input
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.base_dir = base_dir
        self.prediction_horizon = prediction_horizon  # Default horizon of 5 periods
        self.fill_na_method = fill_na_method  # NA fill method passed during initialization
        
        # Initialize the CentralizedDataStorage
        self.data_store = CentralizedDataStorage(user_input)

        # Initialize LoggingMaster
        self.logger = LoggingMaster(f"TimeSeriesForecaster-{self.ticker}").get_logger()

        # Initialize the SelfTeaching module
        self.self_teaching = SelfTeaching(
            model_type="RNN",  # Using RNN for incremental learning
            performance_threshold=0.1, 
            update_frequency=timedelta(seconds=0)
        )

        # Initialize the LIME explainer for model interpretation
        self.lime_explainer = None  # Initialize later after loading data

        # Define U.S. holidays for filtering
        self.holidays = holidays.US()

    def exclude_holidays(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that fall on U.S. holidays."""
        data['date'] = pd.to_datetime(data['date'])
        is_holiday = data['date'].isin(self.holidays)
        non_holiday_data = data[~is_holiday]
        self.logger.info(f"Excluded {len(data) - len(non_holiday_data)} holiday rows from data for {self.ticker}.")
        return non_holiday_data

    def filter_school_breaks(self, data: pd.DataFrame) -> pd.DataFrame:
        """Exclude typical school break times and back-to-school periods."""
        
        current_year = datetime.now().year

        # Winter break: Typically starts a few days before Christmas and ends shortly after New Year's
        winter_break_start = datetime(current_year, 12, 20)
        winter_break_end = datetime(current_year + 1, 1, 10)  # Spans into the next year

        # Summer break: Typically starts at the beginning of June and ends in mid-August
        summer_break_start = datetime(current_year, 6, 1)
        summer_break_end = datetime(current_year, 8, 15)

        # Back-to-school period: Typically late August to early September
        back_to_school_start = datetime(current_year, 8, 15)
        back_to_school_end = datetime(current_year, 9, 15)

        # Exclude these periods dynamically based on the current year
        school_breaks = [
            (winter_break_start, winter_break_end),
            (summer_break_start, summer_break_end),
            (back_to_school_start, back_to_school_end),
        ]
        
        data['date'] = pd.to_datetime(data['date'])
        for start, end in school_breaks:
            data = data[~((data['date'] >= start) & (data['date'] <= end))]

        self.logger.info(f"Excluded school break and back-to-school dates dynamically for the year {current_year}.")
        return data

    def fetch_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch all required data from the central data storage."""
        self.logger.info(f"Fetching data for {self.ticker} from central data storage...")

        # Retrieve data stored for the ticker
        ticker_data = self.data_store.retrieve(self.ticker, "ticker_data")
        
        if ticker_data is None:
            self.logger.error(f"No data found for ticker {self.ticker}")
            return pd.DataFrame(), pd.DataFrame()

        # Extract each specific data type
        historical_data = pd.DataFrame(ticker_data.get("historical_data", []))
        financial_ratios = pd.DataFrame(ticker_data.get("financial_ratios", []))
        
        # Handle data exclusion for holidays and school breaks
        historical_data = self.exclude_holidays(historical_data)
        historical_data = self.filter_school_breaks(historical_data)

        # Combine financial ratios and historical data
        multivariate_data = pd.concat([historical_data, financial_ratios], axis=1)

        return historical_data, multivariate_data

    def _handle_na_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles NA values in the DataFrame based on the method specified by the user."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        if self.fill_na_method == 'mean':
            df.loc[:, numeric_cols] = df.loc[:, numeric_cols].fillna(df[numeric_cols].mean())
        elif self.fill_na_method == 'median':
            df.loc[:, numeric_cols] = df.loc[:, numeric_cols].fillna(df[numeric_cols].median())
        elif self.fill_na_method == 'zero':
            df.loc[:, numeric_cols] = df.loc[:, numeric_cols].fillna(0)
        elif self.fill_na_method == 'interpolate':
            df.loc[:, numeric_cols] = df.loc[:, numeric_cols].interpolate()
        elif self.fill_na_method == 'drop':
            df = df.dropna()
        else:
            self.logger.warning(f"Unknown fill_na_method '{self.fill_na_method}' specified. Defaulting to 'mean'.")
            df.loc[:, numeric_cols] = df.loc[:, numeric_cols].fillna(df[numeric_cols].mean())
        return df

    def forecast_with_models(self) -> Dict[str, Tuple[pd.DataFrame, float, float]]:
        """Performs forecasting using ARIMA, Exponential Smoothing, Theta, XGBoost, and RNN."""
        historical_data, multivariate_data = self.fetch_data()
        
        if historical_data.empty:
            self.logger.warning(f"No historical data available for {self.ticker}.")
            return {}

        series = TimeSeries.from_dataframe(historical_data, time_col='date', value_cols='close')

        # Handle missing values
        series = fill_missing_values(series)

        results = {}

        # ARIMA model
        arima_model = ARIMA()
        arima_model.fit(series)
        arima_forecast = arima_model.predict(self.prediction_horizon)
        results['ARIMA'] = (arima_forecast, arima_model.rmse(), arima_model.mape())

        # Exponential Smoothing model
        exp_model = ExponentialSmoothing()
        exp_model.fit(series)
        exp_forecast = exp_model.predict(self.prediction_horizon)
        results['ExponentialSmoothing'] = (exp_forecast, exp_model.rmse(), exp_model.mape())

        # Theta model
        theta_model = Theta()
        theta_model.fit(series)
        theta_forecast = theta_model.predict(self.prediction_horizon)
        results['Theta'] = (theta_forecast, theta_model.rmse(), theta_model.mape())

        # XGBoost model using multivariate data
        split_index = int(0.8 * len(multivariate_data))
        X_train = multivariate_data.drop(columns='close').iloc[:split_index]
        y_train = multivariate_data['close'].iloc[:split_index]
        X_test = multivariate_data.drop(columns='close').iloc[split_index:]
        y_test = multivariate_data['close'].iloc[split_index:]

        xgb_model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
        xgb_model.fit(X_train, y_train)
        xgb_forecast = xgb_model.predict(X_test)
        rmse = mean_squared_error(y_test, xgb_forecast, squared=False)
        mape = mean_absolute_percentage_error(y_test, xgb_forecast)
        results['XGBoost'] = (xgb_forecast, rmse, mape)

        # RNN model using multivariate data
        rnn_model = RNNModel(model="LSTM", input_chunk_length=12, output_chunk_length=self.prediction_horizon)
        rnn_model.fit(series)
        rnn_forecast = rnn_model.predict(self.prediction_horizon)
        results['RNN'] = (rnn_forecast, rnn_model.rmse(), rnn_model.mape())

        return results


    def explain_with_shap_lime(self, model, X_test: pd.DataFrame, X_train: pd.DataFrame):
        """Generate SHAP and LIME explanations."""
        # SHAP explanation
        explainer = shap.Explainer(model)
        shap_values = explainer(X_test)
        shap.summary_plot(shap_values, X_test)

        # LIME explanation
        self.lime_explainer = LimeTabularExplainer(
            training_data=X_train.values,
            mode='regression'
        )
        lime_explanation = self.lime_explainer.explain_instance(
            data_row=X_test.iloc[0].values,
            predict_fn=model.predict
        )
        self.logger.info(f"LIME explanation for {self.ticker}: {lime_explanation.as_list()}")

    def report_results(self, results: Dict[str, Tuple[pd.DataFrame, float, float

]]):
        """Generate and log the report based on evaluation results."""
        for model_name, (forecast, rmse, mape) in results.items():
            self.logger.info(f"Model: {model_name}, RMSE: {rmse:.4f}, MAPE: {mape:.4f}")

    def run_forecast_and_visualization(self):
        """Run the forecast, evaluate, and visualize the results."""
        results = self.forecast_with_models()
        if results:
            self.report_results(results)
            threading.Thread(target=self.create_and_save_visualization, args=(results, self.ticker)).start()

    def create_and_save_visualization(self, results: Dict[str, Tuple[pd.DataFrame, float, float]], ticker: str):
        """Create and save the forecast visualization using Bokeh."""
        date_str = datetime.today().strftime('%Y-%m-%d')
        output_dir = os.path.join(self.base_dir, ticker, date_str)
        os.makedirs(output_dir, exist_ok=True)

        output_file_name = f"Forecast_{ticker}_{datetime.today().strftime('%Y%m%d')}.html"
        output_file_path = os.path.join(output_dir, output_file_name)

        p = figure(title=f"Forecast for {ticker} - {datetime.today().strftime('%Y-%m-%d')}",
                   x_axis_type="datetime", width=800, height=400)

        # Plot all model forecasts
        for model_name, (forecast, _, _) in results.items():
            p.line(forecast.time_index, forecast.values(), legend_label=model_name)

        # Adding hover tool for better interactivity
        hover = HoverTool(
            tooltips=[("Date", "@x{%F}"), ("Value", "@y{0.2f}")],
            formatters={'@x': 'datetime'},
            mode='vline'
        )
        p.add_tools(hover)
        p.legend.click_policy = "hide"

        # Save plot to HTML file
        save(p, filename=output_file_path)
        self.logger.info(f"Forecast visualization saved at {output_file_path}")

        # Trigger user notification (e.g., a pop-up message)
        self.notify_user_new_forecast(ticker, output_file_path)

    def notify_user_new_forecast(self, ticker: str, file_path: str):
        """Trigger a system notification to inform the user of the new forecast."""
        self.logger.info(f"Notification: New forecast available for {ticker}. File saved at {file_path}")
        
        # Create a system notification
        notification.notify(
            title="New Forecast Available",
            message=f"The forecast for {ticker} has been generated and saved at {file_path}.",
            app_name="Time Series Forecaster",
            timeout=10  # Notification will disappear after 10 seconds
        )

    def runPF(self):
        """The method that orchestrates the entire forecasting process and visualization."""
        self.logger.info(f"Starting forecast process for {self.ticker}...")
        self.run_forecast_and_visualization()
        self.logger.info(f"Forecast process for {self.ticker} completed.")