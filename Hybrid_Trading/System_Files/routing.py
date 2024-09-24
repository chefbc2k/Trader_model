from django.urls import re_path
from .consumers import (
    PortfolioConsumer,
    BacktestProgressConsumer,
    UserInputConsumer,
    ModelTrainerConsumer,
    TradeExecutionConsumer,
    ChartDataConsumer,
    ResultsConsumer
)

websocket_urlpatterns = [
    re_path(r'ws/portfolio/$', PortfolioConsumer.as_asgi()),
    re_path(r'ws/backtest-progress/$', BacktestProgressConsumer.as_asgi()),
    re_path(r'ws/user-input/$', UserInputConsumer.as_asgi()),
    re_path(r'ws/model-trainer/$', ModelTrainerConsumer.as_asgi()),
    re_path(r'ws/trade-execution/$', TradeExecutionConsumer.as_asgi()),
    re_path(r'ws/chart-data/$', ChartDataConsumer.as_asgi()),
    re_path(r'ws/results/$', ResultsConsumer.as_asgi()),
]