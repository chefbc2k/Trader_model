from django.apps import AppConfig
# Data app config
class DataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Data'
    label = 'Data'  # Unique label for the main Data app
