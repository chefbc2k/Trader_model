from django.urls import path
from Hybrid_Trading.Inputs.user_input_view import TaskProgressView, UserInputView  # No need to import GetConfigView anymore

app_name = 'inputs'


urlpatterns = [
    path('user-input/', UserInputView.as_view(), name='user_input'),
    path('task-progress/', TaskProgressView.as_view(), name='task_progress'),
    ]