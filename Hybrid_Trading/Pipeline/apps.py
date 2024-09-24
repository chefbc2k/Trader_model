from django.apps import AppConfig
# Pipeline app config
class PipelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Pipeline'
    label = 'pipeline_app'  # Unique label for the Pipeline app

