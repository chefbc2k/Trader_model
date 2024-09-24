from django.apps import AppConfig

# Backtester app config
class BacktesterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Backtester'
    label = 'backtester_app'  # Unique label for the Backtester app
