from django.urls import path
from .views import StrategyResultsView

app_name = 'strategy'

urlpatterns = [
    path('results/', StrategyResultsView.as_view(), name='strategy_results'),  # No URL parameters now
]