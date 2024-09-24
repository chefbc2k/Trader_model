from threading import Lock
from datetime import datetime
import os
import tempfile
import shutil
from venv import logger
from openpyxl import Workbook, load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
import pandas as pd
import jsonpickle
import hashlib
import shutil
import tempfile
import pickle


USB_BASE_PATH = "/Volumes/tradingdata"

class TempFiles:
    def __init__(self, base_path):
        self.base_path = base_path
        self.temp_dir = self._create_temp_directory()

    def _create_temp_directory(self):
        """
        Creates a temporary directory on the USB drive to handle temporary files.
        If a temp directory already exists, it is removed to avoid stale data.
        """
        try:
            # Ensure base path exists
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)

            # Remove the existing temp directory if it exists
            existing_temp_dir = os.path.join(self.base_path, 'temp_dir')
            if os.path.exists(existing_temp_dir):
                shutil.rmtree(existing_temp_dir)
                print(f"Removed existing temporary directory at: {existing_temp_dir}")

            # Create a new temporary directory
            temp_dir = tempfile.mkdtemp(dir=self.base_path)
            print(f"Temporary directory created at: {temp_dir}")
            return temp_dir

        except IOError as e:
            print(f"Failed to create a temporary directory on the USB drive: {e}")
            return None

    def create_temp_file(self, prefix="temp", suffix=".tmp"):
        """
        Creates a temporary file in the temporary directory on the USB drive.
        Returns the file path.
        """
        if self.temp_dir is None:
            print("Temporary directory is not available. Cannot create temporary file.")
            return None

        try:
            temp_file = tempfile.NamedTemporaryFile(dir=self.temp_dir, prefix=prefix, suffix=suffix, delete=False)
            print(f"Temporary file created at: {temp_file.name}")
            return temp_file.name
        except IOError as e:
            print(f"Failed to create a temporary file on the USB drive: {e}")
            return None

    def save_temp_data(self, data, symbols, filename_prefix='data'):
        """
        Save the temporary data for a list of symbols.
        
        :param data: The data to be saved.
        :param symbols: List of symbols or data related to them.
        :param filename_prefix: Optional prefix for the filename.
        :return: The path of the saved file.
        """
        if not symbols:
            print("No symbols provided. Cannot save data.")
            return None

        # Generate a unique hash for the data to create a filename
        data_hash = hashlib.md5(str(data).encode()).hexdigest()

        # Create a concise filename using a combination of symbols
        if len(symbols) > 1:
            symbols_str = f"{symbols[0]}_to_{symbols[-1]}"
        else:
            symbols_str = symbols[0]

        filename = f"{filename_prefix}_{symbols_str}_{data_hash}.pkl"
        file_path = os.path.join(self.temp_dir, filename)
        
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)

        print(f"Data saved to: {file_path}")
        return file_path

    def load_temp_data(self, symbols, filename_prefix='data'):
        """
        Loads data from a temporary file in the temporary directory.
        
        Parameters:
        - symbols: List of symbols or data related to them.
        - filename_prefix: Optional prefix for the filename.
        
        Returns:
        - The data loaded from the file, or None if loading fails.
        """
        if not symbols:
            print("No symbols provided. Cannot load data.")
            return None

        if len(symbols) > 1:
            symbols_str = f"{symbols[0]}_to_{symbols[-1]}"
        else:
            symbols_str = symbols[0]

        # Search for the file that matches the prefix and symbols
        for file_name in os.listdir(self.temp_dir):
            if file_name.startswith(f"{filename_prefix}_{symbols_str}") and file_name.endswith(".pkl"):
                file_path = os.path.join(self.temp_dir, file_name)
                try:
                    with open(file_path, 'rb') as file:
                        data = pickle.load(file)
                    print(f"Data loaded from: {file_path}")
                    return data
                except IOError as e:
                    print(f"Failed to load data from temporary file: {e}")
                    return None

        print(f"No file found for symbols: {symbols}")
        return None

    def cleanup_temp_files(self):
        """
        Cleans up the temporary directory and its contents.
        """
        if self.temp_dir is None:
            print("Temporary directory is not available. Nothing to clean up.")
            return

        try:
            shutil.rmtree(self.temp_dir)
            print(f"Temporary directory {self.temp_dir} and its contents have been cleaned up.")
            self.temp_dir = None
        except IOError as e:
            print(f"Failed to clean up temporary files on the USB drive: {e}")


class TradingDataWorkbook:
    def __init__(self, ticker, base_path='/Volumes/tradingdata', version="1.0"):
        self.ticker = ticker
        self.base_path = base_path
        self.version = version
        self.workbook_path = self._setup_folder_hierarchy()
        self.save_lock = Lock()  # Ensure thread-safe operations

    def _setup_folder_hierarchy(self):
        """
        Dynamically create and check the folder hierarchy for storing data.
        """
        # Current date as part of the hierarchy
        current_day = datetime.now().strftime('%Y-%m-%d')
        # Create the hierarchy path
        hierarchy_path = os.path.join(self.base_path, current_day, self.ticker)
        # Ensure all directories exist
        if not os.path.exists(hierarchy_path):
            os.makedirs(hierarchy_path, exist_ok=True)
        else:
            print(f"Directory {hierarchy_path} already exists. Adding new data.")
        return hierarchy_path

    def _get_file_path(self, sheet_name):
        """
        Construct the file path based on ticker and sheet name.
        """
        return os.path.join(self.workbook_path, f"{self.ticker}_{sheet_name}.pkl")

    def _validate_data(self, data):
        """
        Validate the data before serialization.
        """
        supported_types = (pd.DataFrame, dict, list, str, int, float, tuple)
        if not isinstance(data, supported_types):
            error_message = (
                f"Unsupported data type for serialization: {type(data)}. "
                f"Supported types are: {supported_types}."
            )
            raise ValueError(error_message)
        return True
    def _calculate_checksum(self, file_path):
        """
        Calculate the SHA-256 checksum of a file.
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256.update(block)
        return sha256.hexdigest()

    def _has_sufficient_space(self, size_needed):
        """
        Check if there is enough disk space available.
        """
        total, used, free = shutil.disk_usage(self.base_path)
        return free >= size_needed

    def save_to_sheet(self, data, sheet_name, serialize=False):
        """
        Save the given DataFrame or data object to a Pickle file.

        Args:
            data: The data to save.
            sheet_name: The name of the sheet (file) to save the data to.
            serialize: If True, the data will be serialized using jsonpickle.
        """
        # Validate the data before serialization
        self._validate_data(data)

        # Serialize if necessary
        if serialize:
            data = jsonpickle.encode(data, unpicklable=False)

        file_path = self._get_file_path(sheet_name)

        # Check for sufficient disk space
        estimated_size = len(pickle.dumps(data))
        if not self._has_sufficient_space(estimated_size):
            raise IOError("Insufficient disk space to save data.")

        # Perform atomic write to a temporary file
        with self.save_lock:
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False, dir=self.workbook_path)
                with temp_file as f:
                    pickle.dump(data, f)
                checksum = self._calculate_checksum(temp_file.name)
                # Rename the temp file to the target file path
                os.rename(temp_file.name, file_path)
                # Verify checksum after rename
                if checksum != self._calculate_checksum(file_path):
                    raise IOError("Checksum mismatch after writing file.")
            finally:
                if temp_file and os.path.exists(temp_file.name):
                    os.remove(temp_file.name)

    def load_from_sheet(self, sheet_name, deserialize=False):
        """
        Load a DataFrame or data object from a Pickle file.

        Args:
            sheet_name: The name of the sheet (file) to load the data from.
            deserialize: If True, the data will be deserialized using jsonpickle.
        """
        file_path = self._get_file_path(sheet_name)
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            if deserialize:
                data = jsonpickle.decode(data)
            return data

    # Specific methods for handling each data type...

    def save_historical_data(self, historical_data):
        self.save_to_sheet(historical_data, "historical_data")

    def save_stock_insights(self, stock_insights):
        self.save_to_sheet(stock_insights, "stock_insights", serialize=True)

    def save_technical_indicators(self, technical_indicators):
        self.save_to_sheet(technical_indicators, "technical_indicators", serialize=True)

    def save_news_scores(self, news_scores):
        self.save_to_sheet(news_scores, "news_scores", serialize=True)

    def save_summary(self, summary):
        self.save_to_sheet(summary, "summary")
    def save_analysis(self, ticker: str, analysis_result: dict[str, any]):
        """
        Save the analysis result to the analysis sheet.

        Args:
            ticker: The ticker symbol associated with the analysis.
            analysis_result: The analysis result data to save.
        """
        self.save_to_sheet(analysis_result, f"analysis_{ticker}")

    # Corresponding methods for loading data...

    def load_historical_data(self):
        return self.load_from_sheet("historical_data")

    def load_stock_insights(self):
        return self.load_from_sheet("stock_insights", deserialize=True)

    def load_technical_indicators(self):
        return self.load_from_sheet("technical_indicators", deserialize=True)

    def load_news_scores(self):
        return self.load_from_sheet("news_scores", deserialize=True)

    def load_summary(self):
        return self.load_from_sheet("summary")

    def create_temp_directory(self):
        """
        Create a temporary directory on the base path for handling temporary files.
        """
        try:
            temp_dir = tempfile.mkdtemp(dir=self.base_path)
            print(f"Temporary directory created at: {temp_dir}")
            return temp_dir
        except IOError as e:
            print(f"Failed to create a temporary directory on the USB drive: {e}")
            return None