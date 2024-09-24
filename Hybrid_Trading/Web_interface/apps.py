from django.apps import AppConfig

class WebInterfaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Web_interface'  # Exact folder path, respecting case
    label = 'Web_interface'  # Keep the label as you prefer (can match folder)