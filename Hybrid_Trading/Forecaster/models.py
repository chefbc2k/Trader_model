from django.db import models  # Import Django's ORM models
from Hybrid_Trading.Symbols.models import Tickers  # Keep your custom Tickers model import

class TimeSeriesForecasts(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')
    interval = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    period = models.CharField(max_length=50, blank=True, null=True)
    prediction_horizon = models.IntegerField(blank=True, null=True)
    fill_na_method = models.CharField(max_length=20, blank=True, null=True)
    forecast_generated_at = models.DateTimeField(blank=True, null=True)
    historical_data = models.JSONField(blank=True, null=True)
    financial_ratios = models.JSONField(blank=True, null=True)
    technical_indicators = models.JSONField(blank=True, null=True)
    arima_forecast = models.JSONField(blank=True, null=True)
    exp_smoothing_forecast = models.JSONField(blank=True, null=True)
    theta_forecast = models.JSONField(blank=True, null=True)
    xgboost_forecast = models.JSONField(blank=True, null=True)
    rnn_forecast = models.JSONField(blank=True, null=True)
    arima_rmse = models.FloatField(blank=True, null=True)
    arima_mape = models.FloatField(blank=True, null=True)
    exp_smoothing_rmse = models.FloatField(blank=True, null=True)
    exp_smoothing_mape = models.FloatField(blank=True, null=True)
    theta_rmse = models.FloatField(blank=True, null=True)
    theta_mape = models.FloatField(blank=True, null=True)
    xgboost_rmse = models.FloatField(blank=True, null=True)
    xgboost_mape = models.FloatField(blank=True, null=True)
    rnn_rmse = models.FloatField(blank=True, null=True)
    rnn_mape = models.FloatField(blank=True, null=True)
    shap_values = models.JSONField(blank=True, null=True)
    lime_explanation = models.JSONField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'time_series_forecasts'