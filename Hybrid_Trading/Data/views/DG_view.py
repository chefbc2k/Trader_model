import asyncio
import logging
import os
import jsonpickle
import pandas as pd
from datetime import datetime
from Hybrid_Trading.Data.Data_Gathering.HD import HistoricalData as FMPDG
from Hybrid_Trading.Analysis.News.news_classifier import NewsClassifier
from Hybrid_Trading.Analysis.News.news import NewsGetter
from Hybrid_Trading.Data.Data_Gathering.FS import FinancialScores
from Hybrid_Trading.Data.Data_Gathering.TI import TechnicalIndicatorFetcher as TechnicalIndicators
from Config.utils import TempFiles  # Assuming TempFiles is in the Utilities directory
from Config.utils import TradingDataWorkbook  # Assuming TradingDataWorkbook is in the same directory
from alive_progress import alive_bar
from asgiref.sync import sync_to_async

class DataGatheringPipeline:
    def __init__(self, form_data):
        """
        Initialize the DataGatheringPipeline with form data.
        """
        self.form_data = form_data
        self.tickers = form_data.get('tickers')
        self.interval = form_data.get('interval')
        self.start_date = form_data.get('start_date')
        self.end_date = form_data.get('end_date')
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.logger = logging.getLogger("DataGatheringPipeline")

    async def process_ticker(self, ticker):
        """
        Process a single ticker asynchronously, fetching historical data, insights, and indicators.
        """
        try:
            self.logger.info(f"Starting data gathering for {ticker}")
            print(f"Starting data gathering for {ticker}")

            # Initialize data gatherers and workbook
            data_gatherer = FMPDG(ticker, self.fmp_api_key, interval=self.interval, start_date=self.start_date, end_date=self.end_date)
            trading_workbook = TradingDataWorkbook(ticker)
            temp_files = TempFiles()

            # Fetch historical data asynchronously
            current_data = await sync_to_async(data_gatherer.get_historical_data)()
            if current_data.empty:
                self.logger.warning(f"No current data available for {ticker}")
                print(f"No current data available for {ticker}")
                return

            # Save historical data to workbook
            await sync_to_async(trading_workbook.save_to_sheet)(current_data, "Historical Data")

            # Generate stock insights
            self.logger.info(f"Generating stock insights for {ticker}")
            print(f"Generating stock insights for {ticker}")
            stock_insights = FinancialScores(ticker, current_data)
            stock_insights.fetch_additional_data()
            insights_data = await sync_to_async(stock_insights.generate_insights)()
            serialized_insights = jsonpickle.encode(insights_data, unpicklable=False)
            await sync_to_async(trading_workbook.save_to_sheet)(serialized_insights, 'Stock Insights')

            # Fetch technical indicators
            self.logger.info(f"Fetching technical indicators for {ticker}")
            print(f"Fetching technical indicators for {ticker}")
            technical_indicators = TechnicalIndicators()
            indicators_data = await sync_to_async(technical_indicators.get_all_indicators)(ticker)
            serialized_indicators = jsonpickle.encode(indicators_data, unpicklable=False)
            await sync_to_async(trading_workbook.save_to_sheet)(serialized_indicators, 'Technical Indicators')

            # Fetch and classify news data
            self.logger.info(f"Gathering and classifying news for {ticker}")
            print(f"Gathering and classifying news for {ticker}")
            news_getter = NewsGetter()
            news_data = await sync_to_async(news_getter.News4export)(ticker, self.start_date, self.end_date)
            news_classifier = NewsClassifier()
            classified_news = await sync_to_async(news_classifier.classify_news)(news_data)
            scores_data = await sync_to_async(news_classifier.calculate_stock_scores)(classified_news)
            serialized_scores = jsonpickle.encode(scores_data, unpicklable=False)
            await sync_to_async(trading_workbook.save_to_sheet)(serialized_scores, 'News Scores')

            self.logger.info(f"News data for {ticker} exported to {trading_workbook.workbook_path}")
            print(f"News data for {ticker} exported to {trading_workbook.workbook_path}")

            # Save summary data
            summary_data = pd.DataFrame({
                'Summary': ['News Scores', 'Stock Insights', 'Technical Indicators'],
                'Data': [len(scores_data), len(insights_data), len(indicators_data)]
            })
            await sync_to_async(trading_workbook.save_to_sheet)(summary_data, "Summary")

            self.logger.info(f"Data gathering completed for {ticker}")
            print(f"Data gathering completed for {ticker}")

            # Clean up temporary files
            await sync_to_async(temp_files.cleanup_temp_files)()

        except Exception as e:
            self.logger.error(f"Error processing data for {ticker}: {e}")
            print(f"Error processing data for {ticker}: {e}")

    async def run_pipeline(self):
        """
        Execute the data gathering pipeline for all tickers in form data.
        """
        # Initialize TempFiles for handling temporary data
        temp_files = TempFiles()

        # Progress bar setup
        async with alive_bar(len(self.tickers), title="Gathering Data for Tickers") as bar:
            tasks = []
            for ticker in self.tickers:
                tasks.append(self.process_ticker(ticker))
                bar()  # Update the progress bar for each ticker processed

            # Run all tasks asynchronously
            await asyncio.gather(*tasks)

        self.logger.info("Data gathering process completed for all tickers.")
        print("Data gathering process completed for all tickers.")

        # Clean up temporary files after processing
        await sync_to_async(temp_files.cleanup_temp_files)()
        self.logger.info("Temporary files cleaned up.")
        print("Temporary files cleaned up.")