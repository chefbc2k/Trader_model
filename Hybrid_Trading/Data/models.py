from django.db import models
from django.utils import timezone  # Correct import
from Hybrid_Trading.Symbols.models import Tickers  # Direct import of Tickers

class Dema(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    dema_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dema'
        unique_together = (('ticker', 'date'),)


class Ema(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    ema_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ema'
        unique_together = (('ticker', 'date'),)


class FinancialRatios(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    current_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    quick_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    cash_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    days_of_sales_outstanding = models.DecimalField(max_digits=14, decimal_places=8)
    days_of_inventory_outstanding = models.DecimalField(max_digits=14, decimal_places=8)
    operating_cycle = models.DecimalField(max_digits=14, decimal_places=8)
    days_of_payables_outstanding = models.DecimalField(max_digits=14, decimal_places=8)
    cash_conversion_cycle = models.DecimalField(max_digits=14, decimal_places=8)
    gross_profit_margin = models.DecimalField(max_digits=14, decimal_places=8)
    operating_profit_margin = models.DecimalField(max_digits=14, decimal_places=8)
    pretax_profit_margin = models.DecimalField(max_digits=14, decimal_places=8)
    net_profit_margin = models.DecimalField(max_digits=14, decimal_places=8)
    effective_tax_rate = models.DecimalField(max_digits=14, decimal_places=8)
    return_on_assets = models.DecimalField(max_digits=14, decimal_places=8)
    return_on_equity = models.DecimalField(max_digits=14, decimal_places=8)
    return_on_capital_employed = models.DecimalField(max_digits=14, decimal_places=8)
    debt_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    debt_equity_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    long_term_debt_to_capitalization = models.DecimalField(max_digits=14, decimal_places=8)
    total_debt_to_capitalization = models.DecimalField(max_digits=14, decimal_places=8)
    interest_coverage = models.DecimalField(max_digits=14, decimal_places=8)
    cash_flow_to_debt_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    company_equity_multiplier = models.DecimalField(max_digits=14, decimal_places=8)
    receivables_turnover = models.DecimalField(max_digits=14, decimal_places=8)
    payables_turnover = models.DecimalField(max_digits=14, decimal_places=8)
    inventory_turnover = models.DecimalField(max_digits=14, decimal_places=8)
    fixed_asset_turnover = models.DecimalField(max_digits=14, decimal_places=8)
    asset_turnover = models.DecimalField(max_digits=14, decimal_places=8)
    operating_cash_flow_per_share = models.DecimalField(max_digits=14, decimal_places=8)
    free_cash_flow_per_share = models.DecimalField(max_digits=14, decimal_places=8)
    cash_per_share = models.DecimalField(max_digits=14, decimal_places=8)
    payout_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    operating_cash_flow_sales_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    free_cash_flow_operating_cash_flow_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    cash_flow_coverage_ratios = models.DecimalField(max_digits=14, decimal_places=8)
    short_term_coverage_ratios = models.DecimalField(max_digits=14, decimal_places=8)
    capital_expenditure_coverage_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    dividend_paid_and_capex_coverage_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    dividend_payout_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_book_value_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_to_book_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_to_sales_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_earnings_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_to_free_cash_flows_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_to_operating_cash_flows_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_cash_flow_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_earnings_to_growth_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    price_sales_ratio = models.DecimalField(max_digits=14, decimal_places=8)
    dividend_yield = models.DecimalField(max_digits=14, decimal_places=8)
    enterprise_value_multiple = models.DecimalField(max_digits=14, decimal_places=8)
    price_fair_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'financial_ratios'
        unique_together = (('ticker', 'date'),)


class FinancialScores(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    altman_z_score = models.DecimalField(max_digits=14, decimal_places=8)
    piotroski_score = models.IntegerField()
    working_capital = models.BigIntegerField()
    total_assets = models.BigIntegerField()
    retained_earnings = models.BigIntegerField()
    ebit = models.BigIntegerField()
    market_cap = models.BigIntegerField()
    total_liabilities = models.BigIntegerField()
    revenue = models.BigIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'financial_scores'
        unique_together = (('ticker', 'altman_z_score'),)


class HistoricalData(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    adj_close = models.FloatField(blank=True, null=True)
    vwap = models.FloatField(blank=True, null=True)
    change = models.FloatField(blank=True, null=True)
    change_percent = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'historical_data'
        unique_together = (('ticker', 'date'),)


class HistoricalPrice(models.Model):
    id = models.AutoField(primary_key=True)  # Set primary_key=True explicitly
    ticker = models.OneToOneField(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    adj_close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    unadjusted_volume = models.BigIntegerField()
    change = models.DecimalField(max_digits=14, decimal_places=8)
    change_percent = models.DecimalField(max_digits=14, decimal_places=8)
    vwap = models.DecimalField(max_digits=14, decimal_places=8)
    label = models.CharField(max_length=50)
    change_over_time = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'historical_price'
        unique_together = (('ticker', 'date'),)


class RealTimePrice(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    bid_size = models.IntegerField()
    ask_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    ask_size = models.IntegerField()
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_sale_size = models.IntegerField()
    last_sale_time = models.BigIntegerField()
    fmp_last = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.BigIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'real_time_price'
        unique_together = (('ticker', 'last_sale_time'),)


class Rsi(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    rsi_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'rsi'
        unique_together = (('ticker', 'date'),)




class TechnicalIndicators(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE)
    sma = models.FloatField(null=True, blank=True)
    ema = models.FloatField(null=True, blank=True)
    rsi = models.FloatField(null=True, blank=True)
    adx = models.FloatField(null=True, blank=True)
    dema = models.FloatField(null=True, blank=True)
    tema = models.FloatField(null=True, blank=True)
    macd = models.FloatField(null=True, blank=True)
    bollingerbands = models.FloatField(null=True, blank=True)
    stochastic = models.FloatField(null=True, blank=True)
    williams = models.FloatField(null=True, blank=True)
    standarddeviation = models.FloatField(null=True, blank=True)
    stdev = models.FloatField(null=True, blank=True)
    variance = models.FloatField(null=True, blank=True)
    momentum = models.FloatField(null=True, blank=True)
    obv = models.FloatField(null=True, blank=True)
    cci = models.FloatField(null=True, blank=True)
    atr = models.FloatField(null=True, blank=True)
    roc = models.FloatField(null=True, blank=True)
    mfi = models.FloatField(null=True, blank=True)
    ultosc = models.FloatField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    period = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)  # Uses Django's timezone.now

    class Meta:
        unique_together = ('ticker', 'date')  # Ensures one entry per ticker per date

    def __str__(self):
        return f"{self.ticker.ticker} - {self.date.isoformat() if self.date else 'No Date'}"

class Tema(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    tema_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tema'
        unique_together = (('ticker', 'date'),)


class Williams(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    williams_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'williams'
        unique_together = (('ticker', 'date'),)


class Wma(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    date = models.DateTimeField()
    wma_value = models.DecimalField(max_digits=14, decimal_places=8)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'wma'
        unique_together = (('ticker', 'date'),)


class TempFiles(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    file_path = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'temp_files'
        unique_together = (('ticker', 'file_path'),)


class ExportLogs(models.Model):
    ticker = models.ForeignKey(Tickers, models.DO_NOTHING, db_column='ticker', to_field='ticker')  # Direct reference to Tickers
    export_path = models.TextField(blank=True, null=True)
    export_timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'export_logs'
        unique_together = (('ticker', 'export_timestamp'),)
        