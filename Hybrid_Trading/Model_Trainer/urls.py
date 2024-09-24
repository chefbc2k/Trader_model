from django.urls import path
from .views import (
    ModelTrainerResultsView,
    ModelTrainerView,  # Updated the view name from OrchestrationView to ModelTrainerView
)

app_name = 'model_trainer'

urlpatterns = [
    # Route to display model training results
    path('model-results/<int:model_training_id>/', ModelTrainerResultsView.as_view(), name='model_trainer_results'),

    # Route to display and handle model trainer form (formerly orchestration)
    path('orchestration/', ModelTrainerView.as_view(), name='orchestration_form'),
]