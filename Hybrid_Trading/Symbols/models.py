# Hybrid_Trading/Symbols/models.py

from django.db import models  # Ensure this import is present


# Define the Tickers model first
class Tickers(models.Model):
    ticker_id = models.AutoField(primary_key=True)
    ticker = models.CharField(unique=True, max_length=10)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Use auto_now_add for automatic timestamp

    class Meta:
        managed = True
        db_table = 'tickers'

# Define the TickerData model, referencing Tickers directly
class TickerData(models.Model):
    ticker = models.ForeignKey(
        Tickers,  # Direct reference since both models are in the same file
        on_delete=models.DO_NOTHING,
        db_column='ticker',
        to_field='ticker'
    )
    data_type = models.CharField(max_length=50)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'ticker_data'
        unique_together = (('ticker', 'data_type'),)