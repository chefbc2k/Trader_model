from django.apps import AppConfig
# Model Trainer app config
class ModelTrainerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hybrid_Trading.Model_Trainer'
    label = 'model_trainer_app'  # Unique label for the Model Trainer app
