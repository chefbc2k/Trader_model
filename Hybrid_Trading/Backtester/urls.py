# urls.py in the app directory (e.g., Hybrid_Trading/urls.py)

from django.urls import path
from . import views

app_name = 'backtester'  # Add this line to define the app_name for namespacing

urlpatterns = [
    path('run_backtest/', views.BacktestView.as_view(), name='run_backtest'),
]