from django.http import JsonResponse
from django.views.generic import FormView, DetailView
from django.shortcuts import render
from tqdm import tqdm
import time
from datetime import timedelta
import pandas as pd
from Hybrid_Trading.Model_Trainer.forms import OrchestrationForm
from Hybrid_Trading.Model_Trainer.MTVIZ import MTVisualization
from Hybrid_Trading.Model_Trainer.models import ModelEvaluation, ModelPrediction, ModelTraining
from Hybrid_Trading.Symbols.SymbolScrapper import TickerScraper
from Hybrid_Trading.Pipeline.MTS import ModelTrainingStage  # Use the correct class for model training
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.trading_constants import TCS
from asgiref.sync import async_to_sync
import json

# Setup logging
logging_master = LoggingMaster("main")
logger = logging_master.get_logger()

class ModelTrainerView(FormView):
    form_class = OrchestrationForm
    template_name = 'model_trainer.html'

    def form_valid(self, form):
        try:
            cleaned_data = form.cleaned_data

            # Initialize TickerScraper with the required 'constants'
            scraper = TickerScraper(constants=TCS)
            all_tickers = scraper.get_all_active_tickers()  # Fetch all active tickers

            # Collect user inputs directly
            user_input = {
                'model_type': cleaned_data['model_type'],
                'tickers': all_tickers,  # Provide all tickers
                'target_column': cleaned_data['target_column'],
                'feature_selection_method': cleaned_data['feature_selection_method'],
                'optimization_method': cleaned_data['optimization_method'],
                'batch_size': cleaned_data['batch_size'],
                'scoring': cleaned_data['scoring'],
                'mape_threshold': cleaned_data.get('mape_threshold'),
                'rmse_threshold': cleaned_data.get('rmse_threshold'),
                'mae_threshold': cleaned_data.get('mae_threshold'),
                'r2_threshold': cleaned_data.get('r2_threshold'),
                'auto_arima_params': cleaned_data['auto_arima_params'],
                'time_series_cv_params': cleaned_data['time_series_cv_params'],
                'custom_weights': cleaned_data.get('custom_weights'),
                'scaling_preference': cleaned_data.get('scaling_preference'),
                'concurrency': cleaned_data.get('concurrency'),
                'return_format': cleaned_data.get('return_format'),
                'start_date': cleaned_data['start_date'].strftime('%Y-%m-%d'),
                'end_date': cleaned_data['end_date'].strftime('%Y-%m-%d'),
                'train_test_split_ratio': cleaned_data['train_test_split_ratio']
            }

            # Initialize the ModelTrainingStage with user inputs
            model_training_stage = ModelTrainingStage(**user_input)

            # Initialize the progress bar and time tracking
            start_time = time.time()
            progress_bar = tqdm(total=len(all_tickers), desc="Processing Tickers", unit="ticker")

            results = []
            for ticker in all_tickers:
                # Track time per ticker and estimate remaining time
                ticker_start_time = time.time()

                # Run the model training process for each ticker
                ticker_result = model_training_stage.run({
                    'ticker': [ticker],
                    'historical_data': pd.DataFrame(),  # Replace with actual historical data
                    'technical_indicators': {}  # Replace with actual indicators data
                })

                # Store the result
                results.append(ticker_result)

                # Update the progress bar
                progress_bar.update(1)

                # Calculate the time taken and estimate remaining time
                elapsed_time_per_ticker = time.time() - ticker_start_time
                total_elapsed_time = time.time() - start_time
                remaining_tickers = len(all_tickers) - progress_bar.n
                estimated_remaining_time = remaining_tickers * elapsed_time_per_ticker

                # Log and display estimated remaining time
                logger.info(f"Estimated remaining time: {timedelta(seconds=estimated_remaining_time)}")
                progress_bar.set_postfix({"Remaining Time": str(timedelta(seconds=estimated_remaining_time))})

                # Send progress updates via WebSocket
                async_to_sync(self.send_message_to_socket)({
                    'progress': int((progress_bar.n / len(all_tickers)) * 100),
                    'message': f"Processing {ticker}: {int((progress_bar.n / len(all_tickers)) * 100)}% complete"
                })

            progress_bar.close()

            # Convert the results list to a DataFrame for rendering
            results_df = pd.DataFrame(results)

            # WebSocket-based completion message
            async_to_sync(self.send_message_to_socket)({
                'progress': 100,  # Mark completion
                'message': 'Model training completed',
                'results': results_df.to_dict(orient='records')
            })

            # Render results and form
            return render(self.request, 'model_trainer.html', {
                'form': form,  # Pass the form back
                'results': results_df.to_dict(orient='records'),  # Ensure JSON serializable format
                'charts': MTVisualization().visualize_forecast(
                    actual=pd.DataFrame(),  # Replace with actual historical data
                    forecast=results_df,  # Pass the forecasted results
                    model_name=user_input['model_type'],
                    ticker=all_tickers,  # Pass the ticker symbol(s)
                    decision="buy/sell"  # Example decision, this should come from logic
                )
            })

        except Exception as e:
            logger.error(f"Error during model training stage: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    async def send_message_to_socket(self, message):
        """
        Sends updates to the WebSocket channel for real-time updates on progress.
        """
        await self.websocket.send_json(message)

    def form_invalid(self, form):
        suggestions = form.errors.as_json()
        return JsonResponse({'suggestions': suggestions}, status=400)
    
class ModelTrainerResultsView(DetailView):
    model = ModelTraining
    template_name = 'model_trainer_results.html'
    context_object_name = 'model_training'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model_training = self.object

        # Get evaluations and predictions associated with the model training
        context['evaluations'] = ModelEvaluation.objects.filter(model_training=model_training)
        context['predictions'] = ModelPrediction.objects.filter(model_training=model_training)

        # Prepare data for visualization if the format is 'html' or 'pdf'
        if self.request.GET.get('return_format') in ['html', 'pdf']:
            actual_data = context['predictions'].values('prediction_date', 'actual_value')
            forecast_data = context['predictions'].values('prediction_date', 'prediction_value')

            mt_visualizer = MTVisualization()
            context['chart'] = mt_visualizer.visualize_forecast(
                actual=actual_data,
                forecast=forecast_data,
                model_name=model_training.model_type
            )

        return context