import pandas as pd
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Hybrid_Trading.Model_Trainer.MTDG import MTDataFetcher  # Import the data fetcher

class MTPreprocessor:
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
                 auto_arima_params: str, 
                 time_series_cv_params: str, 
                 custom_weights: str, 
                 scaling_preference: str, 
                 concurrency: int, 
                 return_format: str, 
                 start_date: str, 
                 end_date: str, 
                 train_test_split_ratio: float):
        """
        Initialize the MTPreprocessor with required parameters.

        Args:
            Various user-defined parameters such as model_type, tickers, etc.
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
        
        self.data_fetcher = MTDataFetcher(self)  # Initialize the data fetcher with the required params
        
        # Initialize logging using LoggingMaster
        logging_master = LoggingMaster("MTPreprocessor")
        self.logger = logging_master.get_logger()
        
        # Validate that the model type is provided
        if not self.model_type:
            self.logger.error("Model type not provided.")
            raise ValueError("Model type is required but not provided.")
        self.logger.info(f"Model type received: {self.model_type}")

    def fetch_and_validate_data(self, ticker: str) -> pd.DataFrame:
        """
        Fetch data from all sources and validate that the DataFrame is not empty.
        
        Parameters:
        - ticker: The stock ticker to fetch data for.
        
        Returns:
        - pd.DataFrame: The fetched data.
        """
        # Fetch data using the MTDataFetcher
        df = self.data_fetcher.fetch_and_preprocess_data_all_sources(ticker)
        self.logger.info(f"Fetched data for {ticker} with columns: {df.columns.tolist()}")

        # Validate that the data is not empty
        if df.empty:
            self.logger.error(f"No data fetched for ticker {ticker}.")
            raise ValueError(f"No data fetched for ticker {ticker}.")

        self.logger.info(f"Fetched and validated data for {ticker}")
        return df

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the data: Handle missing values, apply scaling, and other transformations.
        
        Parameters:
        - df: The data to preprocess.
        
        Returns:
        - pd.DataFrame: The preprocessed data.
        """
        self.logger.info(f"Preprocessing data with initial shape: {df.shape}")

        # Clean the data (Placeholder for actual cleaning logic since dataprep is removed)
        df = self.clean_data(df)
        self.logger.info(f"Data shape after cleaning: {df.shape}")

        self.logger.info(f"Preprocessed data with final shape: {df.shape}")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Custom function to clean the DataFrame: Handle missing values, remove duplicates, etc.
        
        Parameters:
        - df: The DataFrame to clean.
        
        Returns:
        - pd.DataFrame: The cleaned DataFrame.
        """
        # Example cleaning: Removing duplicate rows, handling missing values by filling them with the mean
        df = df.drop_duplicates()
        df = df.fillna(df.mean(numeric_only=True))  # Example: fill missing values with the mean
        return df

    def process_ticker(self, ticker: str) -> pd.DataFrame:
        """
        Fetch, validate, and preprocess data for a single ticker.
        
        Parameters:
        - ticker: The stock ticker to process.
        
        Returns:
        - pd.DataFrame: The final processed data ready for model input.
        """
        try:
            df = self.fetch_and_validate_data(ticker)
            df = self.preprocess_data(df)
            
            self.logger.info(f"Processed data for {ticker}: {df.shape}")
            return df
        except Exception as e:
            self.logger.error(f"Error processing data for {ticker}: {e}")
            return pd.DataFrame()