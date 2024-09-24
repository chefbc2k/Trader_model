from django.views.generic import TemplateView
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Setup logging for LayoutView
logging_master = LoggingMaster("layout_view")
logger = logging_master.get_logger()

class LayoutView(TemplateView):
    template_name = 'layout.html'

    def dispatch(self, request, *args, **kwargs):
        # Log the view being accessed
        logger.info("LayoutView is being rendered")
        return super().dispatch(request, *args, **kwargs)