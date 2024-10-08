# Generated by Django 5.1.1 on 2024-09-14 20:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('symbols_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSeriesForecasts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interval', models.CharField(blank=True, max_length=50, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('period', models.CharField(blank=True, max_length=50, null=True)),
                ('prediction_horizon', models.IntegerField(blank=True, null=True)),
                ('fill_na_method', models.CharField(blank=True, max_length=20, null=True)),
                ('forecast_generated_at', models.DateTimeField(blank=True, null=True)),
                ('historical_data', models.JSONField(blank=True, null=True)),
                ('financial_ratios', models.JSONField(blank=True, null=True)),
                ('technical_indicators', models.JSONField(blank=True, null=True)),
                ('arima_forecast', models.JSONField(blank=True, null=True)),
                ('exp_smoothing_forecast', models.JSONField(blank=True, null=True)),
                ('theta_forecast', models.JSONField(blank=True, null=True)),
                ('xgboost_forecast', models.JSONField(blank=True, null=True)),
                ('rnn_forecast', models.JSONField(blank=True, null=True)),
                ('arima_rmse', models.FloatField(blank=True, null=True)),
                ('arima_mape', models.FloatField(blank=True, null=True)),
                ('exp_smoothing_rmse', models.FloatField(blank=True, null=True)),
                ('exp_smoothing_mape', models.FloatField(blank=True, null=True)),
                ('theta_rmse', models.FloatField(blank=True, null=True)),
                ('theta_mape', models.FloatField(blank=True, null=True)),
                ('xgboost_rmse', models.FloatField(blank=True, null=True)),
                ('xgboost_mape', models.FloatField(blank=True, null=True)),
                ('rnn_rmse', models.FloatField(blank=True, null=True)),
                ('rnn_mape', models.FloatField(blank=True, null=True)),
                ('shap_values', models.JSONField(blank=True, null=True)),
                ('lime_explanation', models.JSONField(blank=True, null=True)),
                ('ticker', models.ForeignKey(db_column='ticker', on_delete=django.db.models.deletion.DO_NOTHING, to='symbols_app.tickers', to_field='ticker')),
            ],
            options={
                'db_table': 'time_series_forecasts',
                'managed': True,
            },
        ),
    ]
