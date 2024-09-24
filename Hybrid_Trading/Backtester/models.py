from django.db import models
from Hybrid_Trading.Symbols.models import Tickers


class BacktestResults(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.DO_NOTHING, db_column='ticker', to_field='ticker')  # ForeignKey to Tickers
    final_portfolio_value = models.FloatField(blank=True, null=True)  # Final value of the portfolio after the backtest
    trade_log = models.JSONField(blank=True, null=True)  # Trade logs as a JSON field
    backtest_date = models.DateTimeField(blank=True, null=True)  # Date when the backtest was conducted

    class Meta:
        db_table = 'Hybrid_Trading_Schema.backtest_results'  # Custom table name for backtest results
        unique_together = (('ticker', 'backtest_date'),)  # Ensure unique combination of ticker and backtest_date

    def __str__(self):
        return f"{self.ticker} - Backtest on {self.backtest_date}"


class BacktestResultsTradeLogs(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, db_column='ticker', to_field='ticker')  # ForeignKey to Tickers
    action = models.CharField(max_length=10)  # Action taken (buy/sell/etc.)
    quantity = models.IntegerField()  # Quantity of shares
    price = models.FloatField()  # Price of the stock at the time of the trade
    date = models.DateTimeField()  # Date and time of the trade
    portfolio_value = models.FloatField()  # Portfolio value after the trade
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the trade was logged

    class Meta:
        db_table = 'Hybrid_Trading_Schema.backtest_results_trade_logs'  # Custom table name
        unique_together = (('ticker', 'date', 'action'),)  # Ensure unique combination of ticker, date, and action
        indexes = [
            models.Index(fields=['ticker', 'date', 'action'], name='idx_bt_logs_tda'),  # Shortened index name for performance
        ]

    def __str__(self):
        return f"{self.ticker} - {self.action} on {self.date}"