import logging
import os
from tqdm import tqdm
from time import time
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.model_trainer_settings import MODEL_SETTINGS
from Hybrid_Trading.Model_Trainer.PLM import PipelineManager  # Import the updated PipelineManager


# Initialize logging for this orchestration module
logging_master = LoggingMaster("orchestration")
logger = logging_master.get_logger()

class Orchestration:
    def __init__(self, 
                 model_type, 
                 tickers,  # Ensure tickers is included here
                 target_column, 
                 feature_selection_method, 
                 optimization_method, 
                 batch_size, 
                 scoring, 
                 mape_threshold, 
                 rmse_threshold, 
                 mae_threshold, 
                 r2_threshold, 
                 auto_arima_params, 
                 time_series_cv_params, 
                 custom_weights, 
                 scaling_preference, 
                 concurrency, 
                 return_format, 
                 start_date, 
                 end_date, 
                 train_test_split_ratio):
        """
        Initialize the orchestration process with the necessary parameters.

        Args:
            model_type (str): The model type selected by the user.
            tickers (list): List of stock tickers to process.
            target_column (str): The target column to predict.
            feature_selection_method (str): Feature selection method (e.g., k_best, mutual_info).
            optimization_method (str): Optimization method (e.g., grid_search, bayesian_optimization).
            batch_size (int): The number of tickers to process in a batch.
            scoring (str): The scoring method chosen by the user.
            Various thresholds, scaling preferences, etc.
        """
        self.model_type = model_type
        self.tickers = tickers  # Assign tickers to the class
        self.target_column = target_column
        self.feature_selection_method = feature_selection_method
        self.optimization_method = optimization_method
        self.batch_size = batch_size
        self.scoring = scoring
        self.mape_threshold = mape_threshold
        self.rmse_threshold = rmse_threshold
        self.mae_threshold = mae_threshold
        self.r2_threshold = r2_threshold
        self.auto_arima_params = auto_arima_params
        self.time_series_cv_params = time_series_cv_params
        self.custom_weights = custom_weights
        self.scaling_preference = scaling_preference
        self.concurrency = concurrency
        self.return_format = return_format
        self.start_date = start_date
        self.end_date = end_date
        self.train_test_split_ratio = train_test_split_ratio
        
        # Initialize the PipelineManager with all the inputs, including tickers
        self.pipeline_manager = PipelineManager(
            model_type=self.model_type,
            tickers=self.tickers,  # Add tickers to PipelineManager
            target_column=self.target_column,
            feature_selection_method=self.feature_selection_method,
            optimization_method=self.optimization_method,
            batch_size=self.batch_size,
            scoring=self.scoring,
            mape_threshold=self.mape_threshold,
            rmse_threshold=self.rmse_threshold,
            mae_threshold=self.mae_threshold,
            r2_threshold=self.r2_threshold,
            auto_arima_params=self.auto_arima_params,
            time_series_cv_params=self.time_series_cv_params,
            custom_weights=self.custom_weights,
            scaling_preference=self.scaling_preference,
            concurrency=self.concurrency,
            return_format=self.return_format,
            start_date=self.start_date,
            end_date=self.end_date,
            train_test_split_ratio=self.train_test_split_ratio
        )

        logger.info(f"Orchestration initialized with model_type: {self.model_type}, "
                    f"tickers: {len(self.tickers)}, batch_size: {self.batch_size}.")
        print(f"Orchestration initialized with {self.model_type}, processing {len(self.tickers)} tickers.")
    def process_batch(self, batch):
        """
        Process a batch of tickers.

        Args:
            batch (list): A list of tickers to process.

        Returns:
            dict: A dictionary containing results for each ticker in the batch.
        """
        results = {}
        for ticker in batch:
            try:
                result = self.pipeline_manager.run_pipeline(ticker, self.target_column)
                if result:
                    results[ticker] = result
                    logger.info(f"Successfully processed {ticker}")
                    print(f"Successfully processed {ticker}")
                else:
                    logger.warning(f"No result for ticker {ticker}")
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        return results

    def orchestrate(self):
        """
        Orchestrate the workflow by processing tickers in batches.
        """
        # Split tickers into batches
        tickers_batches = [self.tickers[i:i + self.batch_size] for i in range(0, len(self.tickers), self.batch_size)]

        logger.info(f"Starting orchestration for {len(tickers_batches)} batches.")
        print(f"Starting orchestration for {len(tickers_batches)} batches.")

        start_time = time()
        results = {}

        for batch in tickers_batches:
            batch_results = self.process_batch(batch)
            results.update(batch_results)

            elapsed_time = time() - start_time
            logger.info(f"Processed batch, elapsed time: {elapsed_time:.2f} seconds")
            print(f"Processed batch, elapsed time: {elapsed_time:.2f} seconds")

        logger.info("Orchestration completed.")
        print("Orchestration completed.")
        return results