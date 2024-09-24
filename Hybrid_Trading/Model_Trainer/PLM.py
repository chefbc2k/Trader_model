import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # Import tqdm for progress bars
from Hybrid_Trading.Model_Trainer.MTDG import MTDataFetcher  # Data Fetcher
from Hybrid_Trading.Model_Trainer.FE import FeatureEngineer  # Feature Engineer
from Hybrid_Trading.Model_Trainer.FS import FeatureSelector  # Feature Selector
from Hybrid_Trading.Model_Trainer.PMA import PerformanceMonitoringAlerts
from Hybrid_Trading.Model_Trainer.Self_Teaching import SelfTeaching # Self-Teaching and Performance Alerts
from Hybrid_Trading.Model_Trainer.MT import TradingModel  # Trading Model
from Hybrid_Trading.Model_Trainer.HPO import HyperOptimization # Hyperparameterization
from Hybrid_Trading.Model_Trainer.MTVIZ import MTVisualization  # MT Visualizer

class PipelineManager:
    def __init__(self, 
                 model_type: str, 
                 tickers: list, 
                 target_column: str, 
                 feature_selection_method: str, 
                 optimization_method: str, 
                 batch_size: int, 
                 scoring: str, 
                 mape_threshold: float, 
                 rmse_threshold: float, 
                 mae_threshold: float, 
                 r2_threshold: float, 
                 auto_arima_params: dict, 
                 time_series_cv_params: dict, 
                 custom_weights: dict, 
                 scaling_preference: str, 
                 concurrency: int, 
                 return_format: str, 
                 start_date: str, 
                 end_date: str, 
                 train_test_split_ratio: float):
        """
        Initialize the PipelineManager with required parameters.
        """
        self.model_type = model_type
        self.tickers = tickers
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
        
        # Initialize all components
        self.data_fetcher = MTDataFetcher(
            tickers=self.tickers,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.feature_engineer = FeatureEngineer(
            custom_weights=self.custom_weights,
            scaling_preference=self.scaling_preference
        )
        
        self.feature_selector = FeatureSelector(
            method=self.feature_selection_method
        )
        
        self.hyper_optimizer = HyperOptimization(
            optimization_method=self.optimization_method,
            scoring=self.scoring,
            auto_arima_params=self.auto_arima_params,
            time_series_cv_params=self.time_series_cv_params
        )
        
        self.trading_model = TradingModel(
            model_type=self.model_type
        )
        
        self.performance_alerts = PerformanceMonitoringAlerts(
            mape_threshold=self.mape_threshold,
            rmse_threshold=self.rmse_threshold,
            mae_threshold=self.mae_threshold,
            r2_threshold=self.r2_threshold
        )
        
        self.self_teaching =  SelfTeaching()
        
        self.visualizer =  MTVisualization ()
        
    def run_pipeline(self):
        """
        Run the complete pipeline across multiple tickers and process them concurrently.

        Returns:
            dict: Results containing evaluation metrics, predictions, and signals for each ticker.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {executor.submit(self.process_ticker, ticker): ticker for ticker in self.tickers}

            with tqdm(total=len(futures), desc="Running Pipeline", ncols=100) as pbar:
                for future in as_completed(futures):
                    ticker = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            results[ticker] = result
                            logging.info(f"Successfully processed {ticker}")
                        else:
                            logging.warning(f"Processing {ticker} returned no result.")
                    except Exception as e:
                        logging.error(f"Error processing {ticker}: {e}")
                    finally:
                        pbar.update(1)

        return results

    def process_ticker(self, ticker: str):
        """
        Process individual ticker through the entire pipeline.

        Args:
            ticker (str): The ticker symbol to process.

        Returns:
            dict: Evaluation metrics, predictions, and signals if successful, otherwise None.
        """
        try:
            # Step 1: Fetch and process data
            df = self.data_fetcher.fetch_and_process_data_all_sources(ticker)
            if df.empty:
                logging.warning(f"No data available after fetching for {ticker}")
                return None

            # Step 2: Feature Engineering
            df = self.feature_engineer.run_feature_engineer(df)
            if df.empty:
                logging.warning(f"No data available after feature engineering for {ticker}")
                return None

            # Step 3: Feature Selection
            df_selected = self.feature_selector.run_selection(df, self.target_column)
            if df_selected.empty:
                logging.warning(f"No data available after feature selection for {ticker}")
                return None

            # Step 4: Split data into training and validation sets
            X_train, X_val, y_train, y_val = self._split_train_validation(df_selected)

            # Step 5: Hyperparameter Optimization
            optimized_params = self.hyper_optimizer.run_hyper_op(X_train, y_train)

            # Step 6: Model Training
            model, evaluation_metrics = self.trading_model.run(
                X_train, y_train, X_val, y_val, optimized_params
            )

            # Step 7: Performance Monitoring and Alerts
            needs_retraining = self.performance_alerts.run(
                model, X_val, y_val
            )

            # Step 8: Self-Teaching (after Performance Monitoring)
            if needs_retraining:
                self.self_teaching.run(
                    model, X_train, y_train, X_val, y_val, evaluation_metrics
                )

            # Step 9: Visualization
            predictions = model.predict(X_val)
            self.visualizer.visualize_forecast(predictions, y_val)

            return {
                "evaluation_metrics": evaluation_metrics,
                "predictions": predictions,
                "signals": None  # Assuming signals are generated within the model
            }

        except Exception as e:
            logging.error(f"Error in process_ticker for {ticker}: {e}")
            return None

    def _split_train_validation(self, df: pd.DataFrame):
        """
        Split the dataset into training and validation sets.

        Args:
            df (pd.DataFrame): The dataset with selected features.

        Returns:
            Tuple of training and validation features and targets.
        """
        train_size = int(len(df) * self.train_test_split_ratio)
        X = df.drop(columns=[self.target_column])
        y = df[self.target_column]

        X_train = X.iloc[:train_size]
        y_train = y.iloc[:train_size]
        X_val = X.iloc[train_size:]
        y_val = y.iloc[train_size:]

        return X_train, X_val, y_train, y_val