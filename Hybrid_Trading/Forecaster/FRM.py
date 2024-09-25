import logging
import os
import time
from typing import List
from dotenv import load_dotenv
from Hybrid_Trading.Daytrader.DTM import DTPipelineOrchestrator
from Config.trading_constants import TCS
from Hybrid_Trading.Symbols.SymbolScrapper import TickerScraper
from Config.utils import TempFiles  # Assuming TempFiles is in a Utilities directory
from Config.utils import TradingDataWorkbook  # Assuming TradingDataWorkbook is in the same directory
from alive_progress import alive_bar
import asyncio

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FullRunPipeline:
    def __init__(self, form_data):
        """
        Initialize the FullRunPipeline with form data and setup orchestration.
        """
        self.form_data = form_data
        self.constants = TCS()
        self.tickers = self.scrape_tickers()  # Fetch tickers during initialization
        self.orchestrator = DTPipelineOrchestrator(form_data)
        self.logger = logging.getLogger("FullRunPipeline")

    def scrape_tickers(self):
        """
        Scrape tickers based on the constants.
        """
        ticker_scraper = TickerScraper(self.constants)
        tickers = ticker_scraper.get_all_active_tickers()
        self.logger.info(f"Scraped tickers: {tickers}")
        return tickers

    async def process_ticker(self, ticker: str):
        """
        Process a single ticker asynchronously using the orchestrator.
        """
        try:
            self.logger.info(f"Processing ticker: {ticker}")

            # Initialize workbook and temporary files management for each ticker
            trading_workbook = TradingDataWorkbook(ticker)
            temp_files = TempFiles()

            # Run the orchestrator pipeline for the current ticker
            await self.orchestrator.run_pipeline()

            # Clean up temporary files after processing
            temp_files.cleanup_temp_files()

            return ticker
        except Exception as e:
            self.logger.error(f"Error processing {ticker}: {e}")
            return None

    async def run_pipeline(self):
        """
        Execute the full pipeline asynchronously using the form data and tickers.
        """
        # Check that API keys are loaded
        alpaca_api_key = os.getenv('APCA_API_KEY_ID')
        alpaca_secret_key = os.getenv('APCA_API_SECRET_KEY')
        fmp_api_key = os.getenv('FMP_API_KEY')

        if not (alpaca_api_key and alpaca_secret_key and fmp_api_key):
            self.logger.error("API keys are not properly set. Please check your environment variables.")
            return

        self.logger.info("Starting full pipeline execution.")

        # Determine number of symbols to process based on form data
        percentage = self.form_data.get("percentage", 100)
        try:
            percentage = int(percentage)
        except ValueError:
            self.logger.error(f"Invalid percentage value: {percentage}")
            percentage = 100  # Fallback to 100% if conversion fails

        num_symbols = len(self.tickers) * percentage // 100
        tickers_to_process = self.tickers[:num_symbols]
        self.logger.info(f"Number of tickers to process: {num_symbols}")

        # Progress bar setup using alive_bar
        async with alive_bar(len(tickers_to_process), title="Processing Tickers") as bar:
            tasks = []
            for ticker in tickers_to_process:
                tasks.append(self.process_ticker(ticker))
                bar()  # Update progress bar for each ticker added

            # Run all tasks asynchronously
            await asyncio.gather(*tasks)

        self.logger.info("Full pipeline execution completed.")
        print("Full pipeline execution completed.")


async def main(form_data):
    """
    Main function to initiate and run the full pipeline based on form data.
    """
    full_run_pipeline = FullRunPipeline(form_data)
    await full_run_pipeline.run_pipeline()