from django.db import models
from django.utils import timezone
from django import forms
# Ticker Reference Table
class Ticker(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.ticker

# User Input Table
class UserInput(models.Model):
    model_type = models.CharField(max_length=50)
    feature_selection_method = models.CharField(max_length=50)
    optimization_method = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    batch_size = models.IntegerField()
    train_test_split_ratio = models.FloatField()
    target_column = models.CharField(max_length=50)
    other_args = models.JSONField()

# Data Source Table
class DataSource(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    data_source_type = models.CharField(max_length=50)
    raw_data_url = models.TextField()
    user_input = models.ForeignKey(UserInput, on_delete=models.CASCADE)

# Preprocessed Data Table
class PreprocessedData(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    feature_engineering_output = models.JSONField()
    feature_selection_output = models.JSONField()
    user_input = models.ForeignKey(UserInput, on_delete=models.CASCADE)

# Model Training Table
class ModelTraining(models.Model):
    model_type = models.CharField(max_length=50)
    hyperparameters = models.JSONField()
    optimization_method = models.CharField(max_length=50)
    best_hyperparameters = models.JSONField()
    user_input = models.ForeignKey(UserInput, on_delete=models.CASCADE)
    training_duration = models.FloatField()

# Model Evaluation Table
class ModelEvaluation(models.Model):
    model_training = models.ForeignKey(ModelTraining, on_delete=models.CASCADE)
    mae = models.FloatField()
    rmse = models.FloatField()
    mape = models.FloatField()
    r2 = models.FloatField()
    evaluation_set = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)

# Model Predictions Table
class ModelPrediction(models.Model):
    model_training = models.ForeignKey(ModelTraining, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    prediction_date = models.DateTimeField()
    prediction_value = models.FloatField()
    actual_value = models.FloatField()
    trade_signal = models.CharField(max_length=10)

# Trade Signals Table
class TradeSignal(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    signal_date = models.DateTimeField()
    signal = models.CharField(max_length=10)
    user_input = models.ForeignKey(UserInput, on_delete=models.CASCADE)

# Self-Teaching Model Update Table
class SelfTeachingUpdate(models.Model):
    model_training = models.ForeignKey(ModelTraining, on_delete=models.CASCADE)
    update_date = models.DateTimeField()
    performance_metric_before = models.FloatField()
    performance_metric_after = models.FloatField()
    reason_for_update = models.CharField(max_length=255)

# Performance Alert Table
class PerformanceAlert(models.Model):
    model_training = models.ForeignKey(ModelTraining, on_delete=models.CASCADE)
    alert_date = models.DateTimeField()
    mape_threshold = models.FloatField()
    rmse_threshold = models.FloatField()
    mae_threshold = models.FloatField()
    r2_threshold = models.FloatField()
    alert_triggered = models.BooleanField()
    retraining_status = models.BooleanField()

# Pipeline Execution Log Table
class PipelineExecutionLog(models.Model):
    user_input = models.ForeignKey(UserInput, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    execution_start_time = models.DateTimeField()
    execution_end_time = models.DateTimeField()
    execution_status = models.CharField(max_length=50)
    log_message = models.TextField()

# Meta classes and Indexes
class Meta:
    indexes = [
        models.Index(fields=['ticker']),
    ]
    
    # Hybrid_Trading/Model_Trainer/forms.py



class OrchestrationForm(forms.Form):
    model_type = forms.CharField(label="Model Type", max_length=100)
    feature_selection_method = forms.CharField(label="Feature Selection Method", max_length=100)
    number_of_features = forms.IntegerField(label="Number of Features")
    optimization_method = forms.CharField(label="Optimization Method", max_length=100)
    scoring = forms.CharField(label="Scoring Method", max_length=100)
    tickers = forms.CharField(label="Tickers")
    target_column = forms.CharField(label="Target Column")
    start_date = forms.DateField(label="Start Date")
    end_date = forms.DateField(label="End Date")
    batch_size = forms.IntegerField(label="Batch Size")
    train_test_split_ratio = forms.FloatField(label="Train/Test Split Ratio")
    auto_arima_params = forms.CharField(label="Auto ARIMA Parameters", required=False)
    time_series_cv_params = forms.CharField(label="Time Series CV Parameters", required=False)
    mape_threshold = forms.FloatField(label="MAPE Threshold")
    rmse_threshold = forms.FloatField(label="RMSE Threshold")
    mae_threshold = forms.FloatField(label="MAE Threshold")
    r2_threshold = forms.FloatField(label="R2 Threshold")
    scaling_preference = forms.CharField(label="Scaling/Normalization Preference")
    custom_weights = forms.CharField(label="Custom Weights", required=False)
    concurrency = forms.IntegerField(label="Concurrency", required=False)
    other_args = forms.CharField(label="Other Arguments", required=False)