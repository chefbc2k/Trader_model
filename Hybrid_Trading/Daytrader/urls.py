from django.urls import path
from Hybrid_Trading.Daytrader.Daytrader_view import TaskProgressView, DaytraderView # No need to import GetConfigView anymore

app_name = 'daytrader'


urlpatterns = [
    path('user-input/', DaytraderView.as_view(), name='DTM'),
    path('task-progress/', TaskProgressView.as_view(), name='task_progress'),
    ]