# Settings page view

from django.views.generic import TemplateView
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Setup logging for BaseView
logging_master = LoggingMaster("base_view")
logger = logging_master.get_logger()

class SettingsView(TemplateView):
    template_name = 'settings.html'