from django.apps import AppConfig
# Modes app config
class ModesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Modes'
    label = 'modes_app'  # Unique label for the Modes app