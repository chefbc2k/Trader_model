from django.views.generic import TemplateView
from Hybrid_Trading.Trading.models import Signals, TradeResults, PerformanceMetrics
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from datetime import datetime
import os

# Setup logging for ResultsView
logging_master = LoggingMaster("results_view")
logger = logging_master.get_logger()

class ResultsView(TemplateView):
    template_name = 'results.html'

    def get_log_content(self, module_name):
        """
        Dynamically reads the log content based on the provided module name.
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_dir = os.path.join('logs', f"{module_name}_{date_str}")
            log_file_path = os.path.join(log_dir, f"{module_name}.log")

            if os.path.exists(log_file_path):
                with open(log_file_path, 'r') as log_file:
                    log_content = log_file.read()
                return log_content
            else:
                logger.warning(f"No log file found for module: {module_name}")
                return f"No log file found for module: {module_name}"
        except Exception as e:
            logger.error(f"Error reading log content: {e}")
            return f"Error reading log for module: {module_name}"

    def get_context_data(self, **kwargs):
        """
        Prepares the initial context and static data for the results view template.
        Dynamic data will be handled via WebSocket connections.
        """
        context = super().get_context_data(**kwargs)

        # Fetch the static log content for the requested module
        module_name = self.request.GET.get('module', 'default_module')
        logger.info(f"Fetching log content for module: {module_name}")
        context['log_content'] = self.get_log_content(module_name)

        # Get the tickers from GET request parameters
        tickers = self.request.GET.getlist('tickers')

        # Filter results based on provided tickers
        if tickers:
            try:
                # Pre-fetch the signals and performance data statically
                signals = Signals.objects.filter(ticker__in=tickers).values('date', 'dynamic_decision')
                performance_metrics = PerformanceMetrics.objects.filter(ticker__in=tickers).values(
                    'sharpe_ratio', 'sortino_ratio', 'max_drawdown', 'volatility', 'annualized_return'
                )
                
                # Pass static data to context
                context['stock_data'] = list(signals)
                context['performance_data'] = list(performance_metrics)
                logger.info(f"Static data fetched for tickers: {tickers}")
            except Exception as e:
                logger.error(f"Error fetching static data: {e}")
                context['error_message'] = "Error fetching data for tickers."
        else:
            logger.warning("No tickers selected.")
            context['error_message'] = "No tickers selected."

        return context