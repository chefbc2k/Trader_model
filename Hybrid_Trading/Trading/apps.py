from django.apps import AppConfig

class TradingInfoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Trading'  # The full Python path to the app
    label = 'trading_info_app'  # This can be anything but must be unique and lowercase