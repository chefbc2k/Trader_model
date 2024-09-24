from django.db import models
from Hybrid_Trading.Symbols.models import Tickers  # Import Tickers for foreign key references

# Model for storing backtesting results for a ticker
class PipelineBacktestResults(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_backtest_results')
    historical_data = models.JSONField()  # Stores the historical data used in backtesting
    prophet_forecast = models.JSONField()  # Stores the Prophet forecast data
    real_time_data = models.JSONField(blank=True, null=True)  # Stores real-time data if available
    technical_indicators = models.JSONField(blank=True, null=True)  # Stores technical indicators if available
    backtest_result = models.JSONField()  # Stores the result of the backtesting process
    status = models.CharField(max_length=20, blank=True, null=True)  # Status (e.g., success or failed)
    reason = models.CharField(max_length=255, blank=True, null=True)  # Reason for failure, if any
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the result was saved

    class Meta:
        managed = True
        db_table = 'pipeline_backtest_results'
        unique_together = (('ticker', 'created_at'),)


# Model to store the real-time progress and logging of the backtesting process
class PipelineBacktestProgress(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_backtest_progress')
    start_time = models.DateTimeField(auto_now_add=True)  # When backtesting started
    estimated_time_remaining = models.FloatField(blank=True, null=True)  # Estimated time left for the task
    completed_tasks = models.IntegerField(default=0)  # Number of tasks completed
    total_tasks = models.IntegerField(default=0)  # Total number of tasks for the ticker
    status = models.CharField(max_length=20, blank=True, null=True)  # Status of the backtesting (e.g., running, completed, failed)
    last_updated = models.DateTimeField(auto_now=True)  # Automatically updated when changes occur

    class Meta:
        managed = True
        db_table = 'pipeline_backtest_progress'
        unique_together = (('ticker', 'start_time'),)


# Model for detailed logging of backtesting process
class PipelineBacktestLogs(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_backtest_logs')
    log_message = models.TextField()  # Store log messages generated during backtesting
    log_level = models.CharField(max_length=20)  # Log level (e.g., info, warning, error)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the log message was created

    class Meta:
        managed = True
        db_table = 'pipeline_backtest_logs'
        unique_together = (('ticker', 'timestamp'),)
        
# Model for storing signals related to trade execution
class PipelineTradeSignals(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_trade_signals')
    dynamic_signals = models.JSONField(blank=True, null=True)  # Store dynamic signals in JSON format
    prediction_signals = models.JSONField(blank=True, null=True)  # Store prediction signals in JSON format
    mrms_signals = models.JSONField(blank=True, null=True)  # Store MRMS signals in JSON format
    vrs_signals = models.JSONField(blank=True, null=True)  # Store VRS signals in JSON format
    trading_signals = models.JSONField(blank=True, null=True)  # Store trading signals in JSON format
    value_seeker_signals = models.JSONField(blank=True, null=True)  # Store value seeker signals in JSON format
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when signals were saved

    class Meta:
        managed = True
        db_table = 'pipeline_trade_signals'
        unique_together = (('ticker', 'created_at'),)


# Model to store the results of the trade execution
class PipelineTradeResults(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_trade_results')
    trade_result = models.JSONField()  # Store the trade result in JSON format
    status = models.CharField(max_length=20, blank=True, null=True)  # Status of the trade (e.g., success, failed)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the trade result was saved

    class Meta:
        managed = True
        db_table = 'pipeline_trade_results'
        unique_together = (('ticker', 'created_at'),)


# Model for logging the trade execution process
class PipelineTradeExecutionLogs(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_trade_execution_logs')
    log_message = models.TextField()  # Log messages related to the trade execution process
    log_level = models.CharField(max_length=20)  # Log level (e.g., info, warning, error)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the log message was created

    class Meta:
        managed = True
        db_table = 'pipeline_trade_execution_logs'
        unique_together = (('ticker', 'timestamp'),)        
        
# Model for storing the input data used in signal generation
class PipelineTickerData(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_ticker_data')
    historical_data = models.JSONField(blank=True, null=True)  # Store historical data in JSON format
    real_time_data = models.JSONField(blank=True, null=True)  # Store real-time data in JSON format
    technical_indicators = models.JSONField(blank=True, null=True)  # Store technical indicators in JSON format
    prophet_forecast = models.JSONField(blank=True, null=True)  # Store Prophet forecast data in JSON format
    financial_ratios = models.JSONField(blank=True, null=True)  # Store financial ratios in JSON format
    financial_scores = models.JSONField(blank=True, null=True)  # Store financial scores in JSON format
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the data was saved

    class Meta:
        managed = True
        db_table = 'pipeline_ticker_data'
        unique_together = (('ticker', 'created_at'),)


# Model to store the generated signals from the various strategies
class PipelineGeneratedSignals(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_generated_signals')
    dynamic_signals = models.JSONField(blank=True, null=True)  # Store dynamic strategy signals in JSON format
    prediction_signals = models.JSONField(blank=True, null=True)  # Store prediction strategy signals in JSON format
    mean_reversion_momentum_signals = models.JSONField(blank=True, null=True)  # Store mean reversion momentum strategy signals in JSON format
    volatility_reversion_signals = models.JSONField(blank=True, null=True)  # Store volatility reversion strategy signals in JSON format
    trading_signals = models.JSONField(blank=True, null=True)  # Store trading strategy signals in JSON format
    value_seeker_signals = models.JSONField(blank=True, null=True)  # Store value seeker strategy signals in JSON format
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the signals were generated

    class Meta:
        managed = True
        db_table = 'pipeline_generated_signals'
        unique_together = (('ticker', 'created_at'),)


# Model for logging the signal generation process
class PipelineSignalGenerationLogs(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_signal_generation_logs')
    log_message = models.TextField()  # Log message related to the signal generation process
    log_level = models.CharField(max_length=20)  # Log level (e.g., info, warning, error)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the log message was created

    class Meta:
        managed = True
        db_table = 'pipeline_signal_generation_logs'
        unique_together = (('ticker', 'timestamp'),)        
        

# Model to store the input data for performance tracking
class PipelinePerformanceInput(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_performance_input')
    trade_results = models.JSONField(blank=True, null=True)  # Store trade results in JSON format
    dynamic_decision = models.CharField(max_length=10, blank=True, null=True, default='Hold')  # Store dynamic decision (e.g., 'Buy', 'Sell', 'Hold')
    prediction_decision = models.CharField(max_length=10, blank=True, null=True, default='Hold')  # Store prediction decision (e.g., 'Buy', 'Sell', 'Hold')
    sentiment_score = models.FloatField(blank=True, null=True, default=0.0)  # Store sentiment score
    weighted_sentiment = models.FloatField(blank=True, null=True, default=0.0)  # Store weighted sentiment score
    analyst_score = models.FloatField(blank=True, null=True, default=0.0)  # Store analyst score
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the input data was saved

    class Meta:
        managed = True
        db_table = 'pipeline_performance_input'
        unique_together = (('ticker', 'created_at'),)


# Model to store the calculated performance metrics for each ticker
class PipelinePerformanceMetrics(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_performance_metrics')
    sharpe_ratio = models.FloatField(blank=True, null=True)  # Store Sharpe Ratio
    sortino_ratio = models.FloatField(blank=True, null=True)  # Store Sortino Ratio
    max_drawdown = models.FloatField(blank=True, null=True)  # Store maximum drawdown
    volatility = models.FloatField(blank=True, null=True)  # Store volatility
    annualized_return = models.FloatField(blank=True, null=True)  # Store annualized return
    alpha = models.FloatField(blank=True, null=True)  # Store alpha
    beta = models.FloatField(blank=True, null=True)  # Store beta
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the metrics were saved

    class Meta:
        managed = True
        db_table = 'pipeline_performance_metrics'
        unique_together = (('ticker', 'created_at'),)


# Model for logging the performance tracking process
class PipelinePerformanceLogs(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker', related_name='pipeline_performance_logs')
    log_message = models.TextField()  # Log message related to performance tracking
    log_level = models.CharField(max_length=20)  # Log level (e.g., info, warning, error)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the log message was created

    class Meta:
        managed = True
        db_table = 'pipeline_performance_logs'
        unique_together = (('ticker', 'timestamp'),)        