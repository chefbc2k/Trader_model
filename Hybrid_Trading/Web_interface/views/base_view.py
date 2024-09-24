from django.views.generic import TemplateView
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Setup logging for BaseView
logging_master = LoggingMaster("base_view")
logger = logging_master.get_logger()

class BaseView(TemplateView):
    template_name = 'base.html'

    def dispatch(self, request, *args, **kwargs):
        # Log the view being accessed
        logger.info("BaseView is being rendered")
        return super().dispatch(request, *args, **kwargs)