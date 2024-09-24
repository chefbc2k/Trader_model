from typing import Dict, Any
import pandas as pd
from Hybrid_Trading.Model_Trainer.MTO import Orchestration
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

class ModelTrainingStage:
    def __init__(self, 
                 model_type, 
                 tickers, 
                 target_column, 
                 feature_selection_method, 
                 optimization_method, 
                 batch_size, 
                 scoring, 
                 mape_threshold=None, 
                 rmse_threshold=None, 
                 mae_threshold=None, 
                 r2_threshold=None, 
                 auto_arima_params=None, 
                 time_series_cv_params=None, 
                 custom_weights=None, 
                 scaling_preference=None, 
                 concurrency=None, 
                 return_format=None, 
                 start_date=None, 
                 end_date=None, 
                 train_test_split_ratio=None):
        """
        Initialize the model training stage with individual parameters.

        Args:
            model_type (str): The model type selected by the user.
            tickers (list): List of stock tickers to process.
            target_column (str): The target column to predict.
            feature_selection_method (str): Feature selection method (e.g., k_best, mutual_info).
            optimization_method (str): Optimization method (e.g., grid_search, bayesian_optimization).
            batch_size (int): The number of tickers to process in a batch.
            scoring (str): The scoring method chosen by the user.
            Other model parameters like thresholds, dates, etc.
        """
        self.logger = LoggingMaster("ModelTrainingStage").get_logger()
        
        # Pass the parameters directly to the Orchestration class
        self.orchestration = Orchestration(
            model_type=model_type,
            tickers=tickers,
            target_column=target_column,
            feature_selection_method=feature_selection_method,
            optimization_method=optimization_method,
            batch_size=batch_size,
            scoring=scoring,
            mape_threshold=mape_threshold,
            rmse_threshold=rmse_threshold,
            mae_threshold=mae_threshold,
            r2_threshold=r2_threshold,
            auto_arima_params=auto_arima_params,
            time_series_cv_params=time_series_cv_params,
            custom_weights=custom_weights,
            scaling_preference=scaling_preference,
            concurrency=concurrency,
            return_format=return_format,
            start_date=start_date,
            end_date=end_date,
            train_test_split_ratio=train_test_split_ratio
        )

    def run(self, fetched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the model training for a given ticker based on fetched data.

        Args:
            fetched_data (dict): Dictionary containing historical data, technical indicators, and other fetched data.

        Returns:
            dict: Updated fetched_data with model training results.
        """
        ticker = fetched_data.get("ticker", "Unknown Ticker")
        self.logger.info(f"Starting model training for {ticker}...")

        try:
            # Ensure historical data and raw indicators are present and correctly formatted
            historical_data = fetched_data.get('historical_data', pd.DataFrame())
            raw_indicators = fetched_data.get('technical_indicators', {}).get('raw_indicators', pd.DataFrame())

            if historical_data.empty or raw_indicators.empty:
                self.logger.warning(f"Missing or empty historical data or raw indicators for {ticker}. Skipping model training.")
                return fetched_data

            # Combine historical data and technical indicators into a single DataFrame
            training_data = pd.DataFrame(historical_data).join(pd.DataFrame(raw_indicators))

            if training_data.empty:
                self.logger.warning(f"Combined training data is empty for {ticker}. Skipping model training.")
                return fetched_data

            # Run the orchestration process
            predictions = self.orchestration.process_batch([ticker])

            # Store the predictions in the fetched_data dictionary
            fetched_data['model_training_results'] = predictions
            self.logger.info(f"Model training completed successfully for {ticker}.")
            return fetched_data

        except Exception as e:
            self.logger.error(f"Error during model training for {ticker}: {e}")
            return None