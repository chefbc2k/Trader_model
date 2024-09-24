from django.db import models
from Hybrid_Trading.Symbols.models import Tickers  # Directly import Tickers


class Signals(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_signals')
    date = models.DateField()
    dynamic_decision = models.JSONField(blank=True, null=True)
    prediction_decision = models.JSONField(blank=True, null=True)
    final_signal = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'signals'
        unique_together = (('ticker', 'date'),)


class StrategySignals(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_strategy_signals')
    strategy_name = models.CharField(max_length=50)
    signal = models.JSONField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'strategy_signals'
        unique_together = (('ticker', 'strategy_name'),)


class SignalAggregates(models.Model):
    ticker = models.OneToOneField(Tickers, models.DO_NOTHING, db_column='ticker', related_name='trading_info_signal_aggregates')
    aggregated_signals = models.JSONField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'signal_aggregates'


class PendingOrders(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_pending_orders')
    quantity = models.IntegerField(blank=True, null=True)
    side = models.CharField(max_length=10, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pending_orders'
        unique_together = (('ticker', 'timestamp'),)


class PerformanceMetrics(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_performance_metrics')
    sharpe_ratio = models.FloatField(blank=True, null=True)
    sortino_ratio = models.FloatField(blank=True, null=True)
    max_drawdown = models.FloatField(blank=True, null=True)
    volatility = models.FloatField(blank=True, null=True)
    annualized_return = models.FloatField(blank=True, null=True)
    alpha = models.FloatField(blank=True, null=True)
    beta = models.FloatField(blank=True, null=True)
    sentiment_score = models.FloatField(blank=True, null=True)
    weighted_sentiment = models.FloatField(blank=True, null=True)
    analyst_score = models.FloatField(blank=True, null=True)
    dynamic_decision = models.CharField(max_length=50, blank=True, null=True)
    prediction_decision = models.CharField(max_length=50, blank=True, null=True)
    calculated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'performance_metrics'
        unique_together = (('ticker', 'calculated_at'),)


class PortfolioManager(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_portfolio_manager')
    position_size = models.IntegerField(blank=True, null=True)
    entry_price = models.FloatField(blank=True, null=True)
    side = models.CharField(max_length=10, blank=True, null=True)
    current_value = models.FloatField(blank=True, null=True)
    profit_loss = models.FloatField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'portfolio_manager'
        unique_together = (('ticker', 'timestamp'),)


class RawTradeData(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_raw_trade_data')
    trade_results = models.JSONField()
    dynamic_decision = models.JSONField(blank=True, null=True)
    prediction_decision = models.JSONField(blank=True, null=True)
    sentiment_score = models.FloatField(blank=True, null=True)
    weighted_sentiment = models.FloatField(blank=True, null=True)
    analyst_score = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_trade_data'
        unique_together = (('ticker', 'created_at'),)


class OrderLog(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_order_log')
    quantity = models.IntegerField(blank=True, null=True)
    side = models.CharField(max_length=10, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_log'
        unique_together = (('ticker', 'timestamp'),)


class TradeResults(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_trade_results')
    dynamic_decision = models.JSONField(blank=True, null=True)
    prediction_decision = models.JSONField(blank=True, null=True)
    instant_backtest_signals = models.JSONField(blank=True, null=True)
    mrms_decision = models.JSONField(blank=True, null=True)
    vrs_decision = models.JSONField(blank=True, null=True)
    sentiment_score = models.FloatField(blank=True, null=True)
    technical_indicator_final_signal = models.CharField(max_length=50, blank=True, null=True)
    insight_final_signal = models.CharField(max_length=50, blank=True, null=True)
    news_final_signal = models.CharField(max_length=50, blank=True, null=True)
    prophet_forecast_signal = models.CharField(max_length=50, blank=True, null=True)
    final_action = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    current_price = models.FloatField(blank=True, null=True)
    order_status = models.CharField(max_length=50, blank=True, null=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trade_results'
        unique_together = (('ticker', 'executed_at'),)


class TradingSignals(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_trading_signals')
    dynamic_signals = models.JSONField(blank=True, null=True)
    prediction_signals = models.JSONField(blank=True, null=True)
    mrms_signals = models.JSONField(blank=True, null=True)
    vrs_signals = models.JSONField(blank=True, null=True)
    trading_signals = models.JSONField(blank=True, null=True)
    value_seeker_signals = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trading_signals'
        unique_together = (('ticker', 'created_at'),)


class BenchmarkData(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_benchmark_data')
    benchmark_name = models.CharField(max_length=50)
    benchmark_returns = models.JSONField()
    calculated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'benchmark_data'
        unique_together = (('ticker', 'calculated_at'),)


class TradeLogs(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='trading_info_trade_logs')
    action = models.CharField(max_length=10)
    quantity = models.IntegerField()
    price = models.FloatField()
    date = models.DateTimeField()
    portfolio_value = models.FloatField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trade_logs'
        unique_together = (('ticker', 'date', 'action'),)