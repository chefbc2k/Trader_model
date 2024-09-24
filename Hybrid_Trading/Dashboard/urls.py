# dashboard/urls.py

from django.urls import path
from . import dashboard_view

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_view.DashboardView.as_view(), name='dashboard'),
]