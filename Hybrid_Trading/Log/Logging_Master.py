import logging
import logging.handlers
import os
from datetime import datetime

LOG_DIR = "logs"
MAX_LOG_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
BACKUP_COUNT = 60

class LoggingMaster:
    def __init__(self, module_name):
        # Handle if module_name is a list of tickers
        if isinstance(module_name, list):
            ticker_count = len(module_name)
            first_ticker = module_name[0] if ticker_count > 0 else "Unknown"
            # Simplified name to avoid overly long filenames
            self.module_name = f"{first_ticker}_and_{ticker_count - 1}_others" if ticker_count > 1 else first_ticker
        else:
            self.module_name = module_name

        self.logger = self.setup_logging()

    def setup_logging(self):
        """
        Set up logging configuration for the entire project with rotating file handlers.
        """
        # Create logs directory if it doesn't exist
        os.makedirs(LOG_DIR, exist_ok=True)

        # Create a module-specific folder based on the current date
        date_str = datetime.now().strftime("%Y-%m-%d")
        module_log_dir = os.path.join(LOG_DIR, f"{self.module_name}_{date_str}")
        os.makedirs(module_log_dir, exist_ok=True)  # Use exist_ok to avoid FileExistsError

        # Set log file paths
        log_file_path = os.path.join(module_log_dir, f"{self.module_name}.log")
        error_log_file_path = os.path.join(module_log_dir, f"{self.module_name}_errors.log")

        # Create a rotating file handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path, maxBytes=MAX_LOG_FILE_SIZE, backupCount=BACKUP_COUNT)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        # Create a rotating file handler for error logs
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file_path, maxBytes=MAX_LOG_FILE_SIZE, backupCount=BACKUP_COUNT)
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        # Create a stream handler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        # Get the logger for the module
        logger = logging.getLogger(self.module_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)
        logger.addHandler(stream_handler)

        # Log the setup completion
        logger.info(f"Logging setup complete for module: {self.module_name}")
        return logger

    def get_logger(self):
        return self.logger
