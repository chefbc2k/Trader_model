import logging
import os
from dotenv import load_dotenv
from django.utils.timezone import now
from django.db import IntegrityError
from Config.trading_constants import TCS
from Hybrid_Trading.Inputs.user_input import UserInput
from Hybrid_Trading.Symbols.SymbolScrapper import TickerScraper
from Hybrid_Trading.Symbols.models import Tickers, TickerData
from Hybrid_Trading.Modes.DGM import run_data_gathering
from Hybrid_Trading.Modes.BTM import run_backtester
from Hybrid_Trading.Modes.FRM import run_full_pipeline
from Hybrid_Trading.Modes.DTM import DTPipelineOrchestrator

# Load environment variables
load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_trading.log'),
        logging.StreamHandler()
    ]
)

def save_ticker_data(ticker_symbol, data_type, data):
    """
    Saves ticker and associated data into the Tickers and TickerData models.

    Parameters:
    - ticker_symbol (str): The ticker symbol to save.
    - data_type (str): The type of data being saved (e.g., 'historical').
    - data (dict): The data to save associated with the ticker.

    Returns:
    - str: The ticker symbol if saved successfully.
    """
    try:
        ticker, created = Tickers.objects.get_or_create(
            ticker=ticker_symbol,
            defaults={'created_at': now()}
        )
        TickerData.objects.create(
            ticker=ticker,
            data_type=data_type,
            data=data,
            created_at=now()
        )
        return ticker.ticker
    except IntegrityError as e:
        logging.error(f"Error saving data for ticker {ticker_symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error saving data for ticker {ticker_symbol}: {str(e)}")
        return None

def run_pipeline(user_input):
    """
    Orchestrates the execution of the pipeline based on user input.

    Parameters:
    - user_input (UserInput): An instance of UserInput containing configuration parameters.
    """
    try:
        # Extract configuration from user_input
        config = user_input.args
        logging.info("Starting pipeline execution.")
        logging.debug(f"User configuration: {config}")

        # Load constants and tickers
        constants = TCS()
        ticker_scraper = TickerScraper(constants)
        all_tickers = ticker_scraper.get_all_active_tickers()
        logging.info(f"Total tickers scraped: {len(all_tickers)}")

        # Determine number of symbols to process based on user input
        percentage = config.get("percentage", 100)
        num_symbols = max(1, len(all_tickers) * percentage // 100)
        tickers_to_process = all_tickers[:num_symbols]
        logging.info(f"Processing {num_symbols} tickers based on user input percentage.")

        # Ensure tickers are included in the user_input args
        user_input.args['tickers'] = tickers_to_process

        # Save tickers to the database
        for ticker_symbol in tickers_to_process:
            data_type = 'historical'  # Placeholder data type
            data = {}  # Replace with actual data fetching logic
            saved_ticker = save_ticker_data(ticker_symbol, data_type, data)
            if saved_ticker:
                logging.debug(f"Data for {saved_ticker} saved successfully.")
            else:
                logging.warning(f"Data for {ticker_symbol} could not be saved.")

        # Load API keys
        alpaca_api_key = os.getenv("APCA_API_KEY_ID")
        alpaca_secret_key = os.getenv("APCA_API_SECRET_KEY")
        fmp_api_key = os.getenv("FMP_API_KEY")

        if not all([alpaca_api_key, alpaca_secret_key, fmp_api_key]):
            logging.error("API keys are not properly set. Please check your environment variables.")
            return

        # Run the appropriate mode
        mode = config.get("mode")
        if mode == 'data_gathering':
            logging.info("Running data gathering mode.")
            run_data_gathering(user_input)
        elif mode == 'backtester':
            logging.info("Running backtester mode.")
            run_backtester(user_input)
        elif mode == 'day_trader':
            logging.info("Running day trader mode.")
            orchestrator = DTPipelineOrchestrator(user_input)
            orchestrator.run_pipeline()
        elif mode == 'full_run':
            logging.info("Running full pipeline mode.")
            run_full_pipeline(user_input)
        else:
            logging.error(
                "Invalid mode selected. Please choose from 'data_gathering', 'backtester', 'day_trader', or 'full_run'."
            )
            return

        logging.info("Pipeline execution completed successfully.")

    except Exception as e:
        logging.exception("An unexpected error occurred during pipeline execution.")

# Note: The run_pipeline function is intended to be called from your Django application,
# such as from a view or a management command.

# Ensure that the modules and functions called within run_pipeline are production-ready and
# do not contain any development or testing code.

# The UserInput class should be properly implemented to handle configurations appropriately.