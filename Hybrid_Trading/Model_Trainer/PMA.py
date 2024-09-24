import logging
from datetime import datetime, timedelta
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score

# Import necessary Django models
from Hybrid_Trading.Trading.models import TradeResults  # Import the TradeResults model
from django.utils import timezone  # For handling time zones

class PerformanceMonitoringAlerts:
    def __init__(self, model, user_input, ticker: str):
        """
        Initialize the performance monitoring system.
        
        :param model: The trained model to monitor
        :param user_input: User configurations and thresholds for monitoring
        :param ticker: The ticker symbol associated with the model
        """
        self.model = model
        self.user_input = user_input
        self.ticker = ticker
        self.metrics_history = []
        self.last_monitor_time = datetime.now() - timedelta(weeks=1)

        # Performance thresholds for retraining
        self.mape_threshold = user_input.get('mape_threshold', 0.1)
        self.rmse_threshold = user_input.get('rmse_threshold', 1.0)
        self.mae_threshold = user_input.get('mae_threshold', 0.5)
        self.r2_threshold = user_input.get('r2_threshold', 0.7)
        
        logging.info("PerformanceMonitoringAlerts initialized.")

    def evaluate_model_performance(self, X_val: pd.DataFrame, y_val: pd.Series):
        """
        Evaluate the model's performance on validation data.
        
        :param X_val: Validation features
        :param y_val: Validation targets
        :return: Dictionary with performance metrics and a boolean flag indicating if retraining is needed
        """
        logging.info("Evaluating model performance for monitoring...")
        predictions = self.model.predict(X_val)
        metrics = {
            'MAE': mean_absolute_error(y_val, predictions),
            'RMSE': mean_squared_error(y_val, predictions, squared=False),
            'MAPE': mean_absolute_percentage_error(y_val, predictions),
            'R-squared': r2_score(y_val, predictions)
        }
        logging.info(f"Model performance metrics: {metrics}")
        self.metrics_history.append(metrics)

        # Check if performance has degraded
        needs_retraining = self._check_performance_degradation(metrics)
        return metrics, needs_retraining

    def _check_performance_degradation(self, metrics: dict):
        """
        Check if the current model performance has degraded beyond acceptable thresholds.
        
        :param metrics: Dictionary of performance metrics
        :return: Boolean flag indicating whether retraining is required
        """
        degradation = (
            metrics['MAPE'] > self.mape_threshold or
            metrics['RMSE'] > self.rmse_threshold or
            metrics['MAE'] > self.mae_threshold or
            metrics['R-squared'] < self.r2_threshold
        )

        if degradation:
            logging.warning("Performance degradation detected. Retraining recommended.")
            return True
        logging.info("Performance within acceptable thresholds.")
        return False

    def run_performance_monitoring(self, X_val: pd.DataFrame, y_val: pd.Series, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Run the performance monitoring process: evaluate performance and decide on retraining.
        
        :param X_val: Validation features
        :param y_val: Validation targets
        :param X_train: Training features (used for retraining if needed)
        :param y_train: Training targets (used for retraining if needed)
        """
        logging.info("Running performance monitoring...")

        # Evaluate model performance
        metrics, needs_retraining = self.evaluate_model_performance(X_val, y_val)

        if needs_retraining:
            logging.info("Initiating model retraining...")
            self.retrain_model(X_train, y_train)
            self.learn_from_trade_execution()

    def retrain_model(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Retrain the model using the provided training data.
        
        :param X_train: Training features
        :param y_train: Training targets
        """
        logging.info("Retraining model...")
        self.model.fit(X_train, y_train)
        logging.info("Model retraining complete.")

    def learn_from_trade_execution(self):
        """
        Learn from the trade executions and update the model accordingly.
        """
        logging.info("Learning from trade execution...")

        # Retrieve trade execution records from the database
        trade_data = self._fetch_trade_execution_data()

        if trade_data.empty:
            logging.warning("No trade execution data available for learning.")
            return

        # Process trade data to create a DataFrame suitable for updating the model
        X_new, y_new = self._process_trade_data(trade_data)

        if X_new.empty or y_new.empty:
            logging.warning("Processed trade data is insufficient for learning.")
            return

        # Update the model incrementally with new data
        self._incremental_model_update(X_new, y_new)

    def _fetch_trade_execution_data(self) -> pd.DataFrame:
        """
        Fetch trade execution data from the database for the specific ticker.
        
        :return: DataFrame containing trade execution data
        """
        logging.info(f"Fetching trade execution data for ticker: {self.ticker}")

        # Get the Ticker object
        from Hybrid_Trading.Symbols.models import Tickers
        ticker_obj = Tickers.objects.get(ticker=self.ticker)

        # Filter trades for the specific ticker and recent period
        one_week_ago = timezone.now() - timedelta(weeks=1)
        trades = TradeResults.objects.filter(
            ticker=ticker_obj,
            executed_at__gte=one_week_ago
        )

        # Convert the queryset to a DataFrame
        if trades.exists():
            trade_df = pd.DataFrame.from_records(trades.values())
            logging.info(f"Fetched {len(trade_df)} trade execution records.")
            return trade_df
        else:
            logging.warning("No trade execution records found.")
            return pd.DataFrame()

    def _process_trade_data(self, trade_data: pd.DataFrame):
        """
        Process trade execution data to extract features and target variables.
        
        :param trade_data: DataFrame containing raw trade execution data
        :return: Tuple of features DataFrame (X_new) and target Series (y_new)
        """
        logging.info("Processing trade execution data for learning...")

        # Handle missing values
        trade_data = trade_data.dropna(subset=['current_price', 'final_action', 'executed_at'])

        # Convert 'executed_at' to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(trade_data['executed_at']):
            trade_data['executed_at'] = pd.to_datetime(trade_data['executed_at'])

        # Convert categorical actions to numerical targets
        action_mapping = {'buy': 1, 'sell': -1, 'hold': 0}
        trade_data['action_numeric'] = trade_data['final_action'].map(action_mapping)

        # Feature engineering
        trade_data['hour'] = trade_data['executed_at'].dt.hour
        trade_data['day_of_week'] = trade_data['executed_at'].dt.dayofweek
        trade_data['sentiment_score'] = trade_data['sentiment_score'].fillna(0.0)
        trade_data['weighted_sentiment'] = trade_data['weighted_sentiment'].fillna(0.0)
        trade_data['analyst_score'] = trade_data['analyst_score'].fillna(0.0)

        # Define features and target
        feature_columns = [
            'current_price', 'hour', 'day_of_week', 'sentiment_score',
            'weighted_sentiment', 'analyst_score'
        ]
        target_column = 'action_numeric'

        X_new = trade_data[feature_columns]
        y_new = trade_data[target_column]

        logging.info("Trade execution data processed successfully.")
        return X_new, y_new

    def _incremental_model_update(self, X_new: pd.DataFrame, y_new: pd.Series):
        """
        Incrementally update the model with new trade execution data.
        
        :param X_new: New features for training
        :param y_new: New target values for training
        """
        logging.info("Incrementally updating the model with new trade data...")

        # Check if the model supports incremental learning
        if hasattr(self.model, 'partial_fit'):
            # For classification, need to specify classes
            if hasattr(self.model, 'classes_'):
                self.model.partial_fit(X_new, y_new)
            else:
                classes = [-1, 0, 1]  # 'sell', 'hold', 'buy'
                self.model.partial_fit(X_new, y_new, classes=classes)
            logging.info("Model updated using partial_fit.")
        else:
            # For models that don't support partial_fit, retrain the model
            logging.info("Model does not support partial_fit. Retraining the model.")
            # Combine existing training data with new data
            X_combined = pd.concat([self.X_train, X_new], ignore_index=True)
            y_combined = pd.concat([self.y_train, y_new], ignore_index=True)
            self.model.fit(X_combined, y_combined)
            logging.info("Model retrained with combined data.")

    def run(self, X_val: pd.DataFrame, y_val: pd.Series, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Master function to run the performance monitoring process.
        
        :param X_val: Validation features
        :param y_val: Validation targets
        :param X_train: Training features
        :param y_train: Training targets
        """
        self.X_train = X_train  # Store training data for potential retraining
        self.y_train = y_train
        self.run_performance_monitoring(X_val, y_val, X_train, y_train)