from django.apps import AppConfig

# Log app config
class LogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Log'
    label = 'log_app'  # Unique label for the Log app
