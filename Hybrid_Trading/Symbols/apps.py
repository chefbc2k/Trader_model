from django.apps import AppConfig
# Symbols app config
class SymbolsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Symbols'
    label = 'symbols_app'  # Unique label for the Symbols app
