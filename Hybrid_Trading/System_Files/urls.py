from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    
    path('', include('Hybrid_Trading.Web_interface.urls', namespace='web_interface')),  # Web Interface
    path('forecaster/', include('Hybrid_Trading.Forecaster.urls', namespace='forecaster')),  # Forecaster
    path('model_trainer/', include('Hybrid_Trading.Model_Trainer.urls', namespace='model_trainer')),  # Model Trainer
    path('inputs/', include('Hybrid_Trading.Inputs.urls', namespace='inputs')),  # Inputs
    path('analysis/', include(('Hybrid_Trading.Analysis.urls', 'analysis'), namespace='analysis')),  # Analysis
    path('strategy/', include('Hybrid_Trading.Strategy.urls', namespace='strategy')),  # Strategy
    path('dashboard/', include('Hybrid_Trading.Dashboard.urls', namespace='dashboard')),  # Dashboard
    path('backtester/', include('Hybrid_Trading.Backtester.urls', namespace='backtester')),  # Backtester
    path('trading/', include('Hybrid_Trading.Trading.urls', namespace='trading')),  # Trading
]