from django.apps import AppConfig

# Dashboard app config
class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Dashboard'
    label = 'dashboard_app'  # Unique label for the Dashboard app