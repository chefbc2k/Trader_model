from django.db import models
from Hybrid_Trading.Symbols.models import Tickers  # Directly import Tickers model


class ValueSeekerSignals(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, db_column='ticker', to_field='ticker')  # Use Tickers directly
    date = models.DateField()
    signal = models.CharField(max_length=10)
    quick_ratio = models.FloatField(blank=True, null=True)
    current_ratio = models.FloatField(blank=True, null=True)
    gross_profit_margin = models.FloatField(blank=True, null=True)
    operating_profit_margin = models.FloatField(blank=True, null=True)
    net_profit_margin = models.FloatField(blank=True, null=True)
    debt_equity_ratio = models.FloatField(blank=True, null=True)
    interest_coverage = models.FloatField(blank=True, null=True)
    price_earnings_ratio = models.FloatField(blank=True, null=True)
    price_book_value_ratio = models.FloatField(blank=True, null=True)
    price_sales_ratio = models.FloatField(blank=True, null=True)
    action = models.CharField(max_length=10)

    class Meta:
        managed = True
        db_table = 'value_seeker_signals'
        unique_together = ('ticker', 'date')
        

class VolatilityReversionSignals(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, db_column='ticker', to_field='ticker')  # Use Tickers directly
    date = models.DateField()
    action = models.CharField(max_length=10)
    reason = models.TextField(blank=True, null=True)
    current_price = models.FloatField()
    upper_band = models.FloatField(blank=True, null=True)
    lower_band = models.FloatField(blank=True, null=True)
    rsi = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'volatility_reversion_signals'
        unique_together = ('ticker', 'date')


class PredictionSignals(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, db_column='ticker', to_field='ticker')  # Use Tickers directly
    date = models.DateField()
    action = models.CharField(max_length=10)
    reason = models.TextField(blank=True, null=True)
    current_price = models.FloatField()
    predicted_today = models.FloatField(blank=True, null=True)
    predicted_5_days_out = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'prediction_signals'
        unique_together = ('ticker', 'date')


class MeanReversionMomentumSignals(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, db_column='ticker', to_field='ticker')  # Use Tickers directly
    date = models.DateField()
    action = models.CharField(max_length=10)
    reason = models.TextField(blank=True, null=True)
    current_price = models.FloatField()
    moving_average = models.FloatField(blank=True, null=True)
    momentum = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'mean_reversion_momentum_signals'
        unique_together = ('ticker', 'date')


class InstantBacktestResults(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, db_column='ticker', to_field='ticker')  # Use Tickers directly
    date = models.DateField()
    signal = models.CharField(max_length=10)
    price = models.FloatField()
    action = models.CharField(max_length=10)

    class Meta:
        managed = True
        db_table = 'instant_backtest_results'
        unique_together = ('ticker', 'date', 'signal')