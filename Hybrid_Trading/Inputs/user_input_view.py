import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from django.http import JsonResponse
from django.views import View
from django.views.generic import FormView
from Hybrid_Trading.Inputs.forms import ConfigurationForm
from Hybrid_Trading.Modes.BTM import BacktesterPipeline
from Hybrid_Trading.Modes.DGM import DataGatheringPipeline
from Hybrid_Trading.Modes.DTM import DTPipelineOrchestrator
from Hybrid_Trading.Modes.FRM import FullRunPipeline
from Hybrid_Trading.Symbols.SymbolScrapper import TickerScraper
from Hybrid_Trading.Symbols.models import Tickers, TickerData  # Import Tickers and TickerData models
from django.db import IntegrityError  # Import IntegrityError to handle database save issues
from django.utils.timezone import now
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.trading_constants import TCS
import uuid  # For generating unique task IDs
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Setup logging
logging_master = LoggingMaster("main")
logger = logging_master.get_logger()

# Define a thread pool executor
executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of workers

class UserInputView(FormView):
    template_name = 'user_input.html'
    form_class = ConfigurationForm
    success_url = '/dashboard/'  # This will be handled via AJAX, so it's not used directly

    def form_valid(self, form):
        """
        Override form_valid to handle scraping tickers, saving them to the database,
        and running the appropriate pipeline in a background thread.
        """
        # Step 1: Gather form data directly
        form_data = form.cleaned_data
        logger.info(f"Form data received: {form_data}")

        # Step 2: Load tickers from form or scraping
        tickers = self.get_tickers()
        logger.info(f"Scraped tickers: {tickers}")

        # Step 3: Process tickers
        self.process_tickers(tickers)

        # Step 4: Dispatch the appropriate pipeline to run in the background using form data
        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        # Define the group name for progress updates
        group_name = f'progress_{task_id}'

        # Run the pipeline in the background
        self.run_pipeline_in_background(form_data, tickers, task_id, group_name)

        # Step 5: Return a JSON response with the task ID
        return JsonResponse({'task_id': task_id})

    def get_tickers(self):
        """ This function should scrape or get the tickers. Replace this logic as needed. """
        # For demonstration, scraping tickers can go here (or you can load tickers from the form)
        constants = TCS()
        ticker_scraper = TickerScraper(constants)
        return ticker_scraper.get_all_active_tickers()

    def process_tickers(self, tickers):
        """ Save tickers to the database and handle IntegrityError """
        for ticker_symbol in tickers:
            try:
                # Create or get the Ticker object
                ticker, created = Tickers.objects.get_or_create(
                    ticker=ticker_symbol,
                    defaults={'created_at': now()}
                )

                # Check if TickerData already exists for this ticker and data_type
                ticker_data_exists = TickerData.objects.filter(ticker=ticker, data_type='historical').exists()

                if not ticker_data_exists:
                    # Create the associated ticker data only if it does not exist
                    TickerData.objects.create(
                        ticker=ticker,
                        data_type='historical',
                        data={},  # Replace with actual data if available
                        created_at=now()
                    )
                    logger.info(f"Data for {ticker_symbol} saved successfully.")
                else:
                    logger.info(f"Data for {ticker_symbol} already exists, skipping.")

            except IntegrityError as e:
                # Handle duplicate entries or any other DB integrity issues
                logger.error(f"Error saving data for ticker {ticker_symbol}: {str(e)}")

    def run_pipeline_in_background(self, form_data, tickers, task_id, group_name):
        """
        Dispatch the appropriate pipeline to run in the background using ThreadPoolExecutor.
        Also send progress updates via Channels to the specified group.
        """
        mode = form_data.get("mode")
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")
        fillna_method = form_data.get("fillna_method")
        sentiment_type = form_data.get("sentiment_type")
        interval = form_data.get("interval", "1d")
        period = form_data.get("period", "D")

        logger.info(f"Running pipeline in mode: {mode} with parameters: start_date={start_date}, end_date={end_date}, "
                    f"interval={interval}, period={period}, fillna_method={fillna_method}, sentiment_type={sentiment_type}")

        # Define a nested function to run the pipeline and send progress
        def run_pipeline():
            try:
                channel_layer = get_channel_layer()

                if mode == 'full_run':
                    full_pipeline = FullRunPipeline(tickers, interval, start_date, end_date, fillna_method, sentiment_type, task_id)
                    asyncio.run(full_pipeline.run_pipeline())
                elif mode == 'backtester':
                    backtester_pipeline = BacktesterPipeline(tickers, interval, start_date, end_date, fillna_method, sentiment_type, task_id)
                    asyncio.run(backtester_pipeline.run_pipeline())
                elif mode == 'day_trader':
                    orchestrator = DTPipelineOrchestrator(
                        tickers, interval, start_date, end_date, period, fillna_method, sentiment_type
                    )
                    asyncio.run(orchestrator.run_day_trading_pipeline(task_id))
                elif mode == 'data_gathering':
                    data_gathering_pipeline = DataGatheringPipeline(
                        tickers, interval, start_date, end_date, fillna_method, sentiment_type, task_id
                    )
                    asyncio.run(data_gathering_pipeline.run_pipeline())
                else:
                    logger.error(f"Invalid mode selected: {mode}")
                    # Update progress to indicate failure
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'progress_update',
                            'status': 'error',
                            'progress': 100,
                            'message': f"Invalid mode selected: {mode}"
                        }
                    )
                    return

                # After successful completion
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'progress_update',
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Processing complete.'
                    }
                )

            except Exception as e:
                logger.error(f"Error running {mode} pipeline: {e}")
                # Update progress to indicate failure
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'progress_update',
                        'status': 'error',
                        'progress': 100,
                        'message': str(e)
                    }
                )

        # Submit the pipeline to run in background
        executor.submit(run_pipeline)

class TaskProgressView(View):
    def get(self, request):
        task_id = request.GET.get('task_id')
        if not task_id:
            return JsonResponse({'error': 'No task_id provided'}, status=400)
        
        task_info = cache.get(task_id)
        if not task_info:
            return JsonResponse({'error': 'Invalid task_id'}, status=400)
        
        return JsonResponse(task_info)