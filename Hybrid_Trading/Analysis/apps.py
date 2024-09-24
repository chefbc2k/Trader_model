from django.apps import AppConfig
# Analysis app config
class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Analysis'
    label = 'analysis_app'  # Unique label for the Analysis app