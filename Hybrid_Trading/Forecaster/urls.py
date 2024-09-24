from django.urls import path
from .views import ForecastView  # Import the class-based view

app_name = 'forecaster'  # Define the app name for namespacing

urlpatterns = [
    path('forecast/', ForecastView.as_view(), name='forecast'),  # Use the class-based view
]