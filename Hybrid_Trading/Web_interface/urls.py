from django.urls import include, path
from .views import (
    IndexView, SettingsView, LayoutView, BaseView,  
)

app_name = 'web_interface'  # Defining the app namespace

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('layout/', LayoutView.as_view(), name='layout'),
    path('base/', BaseView.as_view(), name='base'),


    # path('forecast/', ForecastView.as_view(), name='forecast'),  # Example if you have a ForecastView
]