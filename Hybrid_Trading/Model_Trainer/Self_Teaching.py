import logging
from datetime import datetime, timedelta
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.exceptions import NotFittedError
from darts import TimeSeries
from darts.models import RNNModel
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Import the necessary Django models
from Hybrid_Trading.Model_Trainer.models import (
    ModelEvaluation,
    ModelPrediction,
    TradeSignal,
    SelfTeachingUpdate,
    ModelTraining,
    UserInput,
    Ticker
)
from django.utils import timezone

class SelfTeaching:
    def __init__(self, model, tickers: str):
        """
        Initialize the self-teaching model with configuration parameters.

        Parameters:
        - model: The initial trained model.
        - tickers: The stock ticker(s) associated with the model.
        """
        self.model = model
        self.ticker = tickers
        self.metrics_history = []
        self.last_update = datetime.now() - timedelta(weeks=1)
        
        # Default performance thresholds
        self.performance_threshold = {
            'MAPE': 0.1,  # Default threshold for Mean Absolute Percentage Error
            'MSE': 1.0,   # Default threshold for Mean Squared Error
            'MAE': 0.5    # Default threshold for Mean Absolute Error
        }

        logging.info(f"Initialized SelfTeaching class for ticker {self.ticker} with default performance thresholds.")

    def incremental_fit(self, new_data: pd.DataFrame, target_column: str):
        """
        Perform incremental fitting of the model with new data.

        Parameters:
        - new_data: The new data to incorporate into the model.
        - target_column: The column in the DataFrame that contains the target variable.
        """
        try:
            if new_data.empty:
                logging.warning("No new data available for incremental fit.")
                return

            X_new = new_data.drop(columns=[target_column])
            y_new = new_data[target_column]

            if isinstance(self.model, SGDRegressor):
                # Perform incremental learning for SGDRegressor
                self.model.partial_fit(X_new, y_new)
                logging.info("SGDRegressor model incrementally updated with new data.")
            elif isinstance(self.model, RNNModel):
                # Fit the RNN model (since Darts doesn't directly support partial_fit)
                series = TimeSeries.from_dataframe(new_data, time_col='date', value_cols=target_column)
                self.model.fit(series)
                logging.info("RNN model updated with new data.")
        except Exception as e:
            logging.error(f"Error during incremental fit: {e}")

    def check_performance(self, test_data: pd.DataFrame, target_column: str):
        """
        Check the current performance of the model.

        Parameters:
        - test_data: The DataFrame containing test data.
        - target_column: The column in the DataFrame that contains the target variable.

        Returns:
        - dict: A dictionary with performance metrics (e.g., MAPE, MSE, MAE).
        """
        try:
            if test_data.empty:
                logging.warning("No test data available to check performance.")
                return {"MAPE": float('inf'), "MSE": float('inf'), "MAE": float('inf')}

            X_test = test_data.drop(columns=[target_column])
            y_test = test_data[target_column]

            # Check if the model is fitted before prediction
            try:
                y_pred = self.model.predict(X_test) if isinstance(self.model, SGDRegressor) else self.model.predict(n=len(y_test))
            except NotFittedError:
                logging.warning("Model is not fitted yet. Fitting the model before prediction.")
                # Fit the model with the first batch of test data as a fallback
                self.incremental_fit(test_data, target_column)
                y_pred = self.model.predict(X_test)

            mape = mean_absolute_percentage_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)

            # Record the performance metrics
            self.record_evaluation(mape, mse, mae)

            return {"MAPE": mape, "MSE": mse, "MAE": mae}
        except Exception as e:
            logging.error(f"Error during performance check: {e}")
            return {"MAPE": float('inf'), "MSE": float('inf'), "MAE": float('inf')}

    def record_signal(self, ticker: str, predictions: pd.Series, actuals: pd.Series):
        """
        Record the signal prediction for later analysis and learning.

        Parameters:
        - ticker: The stock ticker associated with the prediction.
        - predictions: The predictions made by the model.
        - actuals: The actual values of the target variable.
        """
        logging.info(f"Recording signals for {ticker}.")

        # Get the Ticker and UserInput instances
        ticker_obj = Ticker.objects.get(ticker=ticker)
        user_input_obj = UserInput.objects.get(id=self.user_input.get('id'))

        # Assuming we have a ModelTraining instance associated with this model
        model_training_obj = ModelTraining.objects.filter(user_input=user_input_obj).last()

        # Record predictions and trade signals
        for pred_date, pred_value, actual_value in zip(actuals.index, predictions, actuals):
            # Determine trade signal
            trade_signal = 'BUY' if pred_value > actual_value else 'SELL' if pred_value < actual_value else 'HOLD'

            # Create ModelPrediction entry
            ModelPrediction.objects.create(
                model_training=model_training_obj,
                ticker=ticker_obj,
                prediction_date=pred_date,
                prediction_value=pred_value,
                actual_value=actual_value,
                trade_signal=trade_signal
            )

            # Create TradeSignal entry
            TradeSignal.objects.create(
                ticker=ticker_obj,
                signal_date=pred_date,
                signal=trade_signal,
                user_input=user_input_obj
            )

        logging.info(f"Signals recorded for {ticker}.")

    def record_evaluation(self, mape, mse, mae):
        """
        Record the model's evaluation metrics.

        Parameters:
        - mape: Mean Absolute Percentage Error.
        - mse: Mean Squared Error.
        - mae: Mean Absolute Error.
        """
        logging.info("Recording model evaluation metrics.")

        # Get the UserInput and ModelTraining instances
        user_input_obj = UserInput.objects.get(id=self.user_input.get('id'))
        model_training_obj = ModelTraining.objects.filter(user_input=user_input_obj).last()

        # Create ModelEvaluation entry
        ModelEvaluation.objects.create(
            model_training=model_training_obj,
            mae=mae,
            rmse=mse ** 0.5,
            mape=mape,
            r2=None,  # Assuming R^2 is not calculated here
            evaluation_set='SelfTeaching',
            timestamp=timezone.now()
        )

    def learn_from_order_execution(self):
        """
        Learn from the order execution details to refine the model.
        """
        logging.info("Learning from order execution...")

        # Fetch recent trade signals and actual trade results
        one_week_ago = timezone.now() - timedelta(weeks=1)
        trade_signals = TradeSignal.objects.filter(
            ticker__ticker=self.ticker,
            signal_date__gte=one_week_ago
        )

        # Process the trade signals and update the model
        if trade_signals.exists():
            # Convert to DataFrame
            signals_df = pd.DataFrame.from_records(trade_signals.values())
            # For simplicity, let's assume we have features and targets in signals_df
            # Update the model with new data
            self.incremental_fit(signals_df, target_column='signal')
            logging.info("Model updated based on order execution data.")
        else:
            logging.warning("No recent trade signals found for learning.")

    def decide_update(self, performance_metrics: dict):
        """
        Decide whether to update the model based on the current performance metrics.

        Returns:
        - bool: Whether the model should be updated.
        """
        degradation = (
            performance_metrics['MAPE'] > self.performance_threshold['MAPE'] or
            performance_metrics['MSE'] > self.performance_threshold['MSE'] or
            performance_metrics['MAE'] > self.performance_threshold['MAE']
        )

        logging.info(f"Model update decision: {'Update needed' if degradation else 'No update required'}")
        return degradation

    def update_model(self, new_data: pd.DataFrame, target_column: str):
        """
        Update the model with new data if conditions are met.

        Parameters:
        - new_data: The new data to incorporate into the model.
        - target_column: The column in the DataFrame that contains the target variable.
        """
        if not new_data.empty:
            self.incremental_fit(new_data, target_column)
            logging.info("Model updated with new data.")

            # Record the self-teaching update
            self.record_self_teaching_update()
        else:
            logging.info("No new data available for update.")

    def record_self_teaching_update(self):
        """
        Record the self-teaching update information to the database.
        """
        logging.info("Recording self-teaching update.")

        # Get the UserInput and ModelTraining instances
        user_input_obj = UserInput.objects.get(id=self.user_input.get('id'))
        model_training_obj = ModelTraining.objects.filter(user_input=user_input_obj).last()

        # Assuming we have access to performance metrics before and after
        if len(self.metrics_history) >= 2:
            performance_metric_before = self.metrics_history[-2]['MAPE']
            performance_metric_after = self.metrics_history[-1]['MAPE']
        else:
            performance_metric_before = None
            performance_metric_after = self.metrics_history[-1]['MAPE'] if self.metrics_history else None

        # Create SelfTeachingUpdate entry
        SelfTeachingUpdate.objects.create(
            model_training=model_training_obj,
            update_date=timezone.now(),
            performance_metric_before=performance_metric_before,
            performance_metric_after=performance_metric_after,
            reason_for_update='Automatic self-teaching based on performance degradation.'
        )

    def run(self, test_data: pd.DataFrame, target_column: str, new_data: pd.DataFrame = None):
        """
        Main loop to run the self-teaching mechanism.

        Parameters:
        - test_data: The DataFrame containing test data.
        - target_column: The column in the DataFrame that contains the target variable.
        - new_data: New data to update the model with.
        """
        performance_metrics = self.check_performance(test_data, target_column)
        logging.info(f"Current performance: {performance_metrics}")

        if self.decide_update(performance_metrics):
            logging.info("Model update triggered based on performance.")
            if new_data is not None:
                self.update_model(new_data, target_column)
            else:
                logging.warning("No new data provided for model update.")
        else:
            logging.info("No update required at this time.")

        # Learn from order executions
        self.learn_from_order_execution()