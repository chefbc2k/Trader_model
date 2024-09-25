import asyncio
from linecache import cache
import uuid
from concurrent.futures import ThreadPoolExecutor
from django.http import JsonResponse
from django.views import View
from Hybrid_Trading.Daytrader.forms import DaytraderForm
from Hybrid_Trading.Daytrader.DTM import DTPipelineOrchestrator  # Only keeping the relevant pipeline orchestrator
from Hybrid_Trading.Symbols.SymbolScrapper import TickerScraper
from Hybrid_Trading.Symbols.models import Tickers, TickerData
from django.db import IntegrityError
from django.utils.timezone import now
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.trading_constants import TCS
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.shortcuts import render

# Setup logging
logging_master = LoggingMaster("main")
logger = logging_master.get_logger()

# Define a thread pool executor
executor = ThreadPoolExecutor(max_workers=5)  # Adjust based on your requirements

class DaytraderView(View):
    template_name = 'user_input.html'
    form_class = DaytraderForm
    success_url = '/dashboard/'

    """
    Handles user input via GET (to render form) and POST (to process form via AJAX).
    """

    # Add the GET method to render the form
    def get(self, request, *args, **kwargs):
        form = self.form_class()  # Initialize an empty form
        # Explicitly pass form_class to the context
        context = {
            'form': form,
            'form_class': self.form_class,  # Adding form_class to the context
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Step 1: Gather form data
            form_data = form.cleaned_data
            logger.info(f"Form data received: {form_data}")

            # Step 2: Scrape or retrieve tickers
            tickers = self.get_tickers()
            logger.info(f"Scraped tickers: {tickers}")

            # Step 3: Save tickers to the database
            self.process_tickers(tickers)

            # Step 4: Generate a unique task ID and group name for Channels
            task_id = str(uuid.uuid4())
            group_name = f'progress_{task_id}'

            # Step 5: Start the pipeline in a background thread
            self.run_pipeline_in_background(form_data, tickers, task_id, group_name)

            # Step 6: Respond with the task ID
            return JsonResponse({'task_id': task_id}, status=200)
        else:
            # Return form errors
            errors = form.errors.as_json()
            return JsonResponse({'errors': json.loads(errors)}, status=400)

    def get_tickers(self):
        """
        Scrape or retrieve tickers. Replace the logic as needed.
        """
        constants = TCS()
        ticker_scraper = TickerScraper(constants)
        return ticker_scraper.get_all_active_tickers()

    def process_tickers(self, tickers):
        """
        Save tickers and their data to the database.
        """
        for ticker_symbol in tickers:
            try:
                # Create or get the Ticker object
                ticker, created = Tickers.objects.get_or_create(
                    ticker=ticker_symbol,
                    defaults={'created_at': now()}
                )

                # Check if TickerData exists
                if not TickerData.objects.filter(ticker=ticker, data_type='historical').exists():
                    # Create TickerData
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
                logger.error(f"Error saving data for ticker {ticker_symbol}: {str(e)}")

    def run_pipeline_in_background(self, form_data, tickers, task_id, group_name):
        """
        Dispatch the appropriate pipeline to run in the background.
        Sends progress updates via Channels.
        """
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")
        fillna_method = form_data.get("fillna_method")
        sentiment_type = form_data.get("sentiment_type")
        interval = form_data.get("interval", "1d")
        period = form_data.get("period", "D")

        logger.info(f"Running day trader pipeline with parameters: start_date={start_date}, end_date={end_date}, "
                    f"interval={interval}, period={period}, fillna_method={fillna_method}, sentiment_type={sentiment_type}")

        def run_pipeline():
            try:
                channel_layer = get_channel_layer()

                # Using only the DTPipelineOrchestrator for running the day trader pipeline
                orchestrator = DTPipelineOrchestrator(
                    tickers, interval, start_date, end_date, period, fillna_method, sentiment_type
                )
                asyncio.run(orchestrator.run_day_trading_pipeline(task_id))

                # After successful completion
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'progress_update',
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Day trader pipeline completed successfully.'
                    }
                )

            except Exception as e:
                logger.error(f"Error running day trader pipeline: {e}")
                # Send error message via Channels
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'progress_update',
                        'status': 'error',
                        'progress': 100,
                        'message': str(e)
                    }
                )

        # Submit the pipeline to run in the background
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