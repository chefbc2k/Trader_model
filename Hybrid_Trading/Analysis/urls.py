from django.urls import path
from .views import NewsAnalysisView

urlpatterns = [
    path('analysis/news/', NewsAnalysisView.as_view(), name='news_analysis'),
]