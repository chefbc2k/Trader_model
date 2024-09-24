from django.apps import AppConfig
# Forecaster app config
class ForecasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Forecaster'
    label = 'forecaster_app'  # Unique label for the Forecaster app
