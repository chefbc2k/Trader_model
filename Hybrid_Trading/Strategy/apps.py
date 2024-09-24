from django.apps import AppConfig
# Strategy app config
class StrategyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Strategy'
    label = 'strategy_app'  # Unique label for the Strategy app
