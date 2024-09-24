from django.urls import path
from Hybrid_Trading.Trading.views import ResultsView
from Hybrid_Trading.Trading.views.portfolio_view import PortfolioView


app_name = 'trading'  # Defining the app namespace

urlpatterns = [
    path('results/', ResultsView.as_view(), name='results'),
    path('portfolio/', PortfolioView.as_view(), name='portfolio'),  
  
]