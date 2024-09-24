import logging
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

class TradingModel:
    def __init__(self, model):
        """
        Initialize the TradingModel class with a specific model.
        
        :param model: Pre-initialized machine learning model (passed from the pipeline).
        """
        self.model = model
        logging.info("TradingModel initialized with model: {}".format(self.model))

    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Train the model using provided training data.
        """
        logging.info("Training model...")
        self.model.fit(X_train, y_train)
        logging.info("Model training complete.")

    def evaluate_model(self, X_val: pd.DataFrame, y_val: pd.Series):
        """
        Evaluate the model's performance on the validation dataset.
        
        :param X_val: Validation feature set
        :param y_val: Validation target set
        :return: Dictionary containing performance metrics (MAE and RMSE)
        """
        logging.info("Evaluating model...")
        predictions = self.model.predict(X_val)
        mae = mean_absolute_error(y_val, predictions)
        rmse = mean_squared_error(y_val, predictions, squared=False)
        logging.info(f"Model evaluation complete. MAE: {mae}, RMSE: {rmse}")
        return {'MAE': mae, 'RMSE': rmse}

    def generate_trade_signals(self, predictions: pd.Series, threshold_buy: float = 0.02, threshold_sell: float = -0.02):
        """
        Generate trade signals (buy, sell, or hold) based on predictions.
        
        :param predictions: Predicted values from the model
        :param threshold_buy: Buy threshold for generating buy signals
        :param threshold_sell: Sell threshold for generating sell signals
        :return: A Series of trade signals (buy, sell, or hold)
        """
        logging.info("Generating trade signals...")
        signals = pd.Series(index=predictions.index, dtype="object")
        signals[predictions > threshold_buy] = 'buy'
        signals[predictions < threshold_sell] = 'sell'
        signals[(predictions <= threshold_buy) & (predictions >= threshold_sell)] = 'hold'
        logging.info(f"Trade signals generated: {signals.value_counts().to_dict()}")
        return signals

    def run(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series):
        """
        Execute the full pipeline for the model: train, evaluate, and generate trade signals.
        """
        logging.info("Running full pipeline for model...")
        self.train_model(X_train, y_train)
        evaluation_metrics = self.evaluate_model(X_val, y_val)
        predictions = self.model.predict(X_val)
        signals = self.generate_trade_signals(predictions)
        logging.info("Full pipeline execution complete.")
        return evaluation_metrics, predictions, signals