from django.apps import AppConfig

# Inputs app config
class InputsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Inputs'
    label = 'inputs_app'  # Unique label for the Inputs app