from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

from Hybrid_Trading.Symbols.models import Tickers
# Import Tickers model from the Symbols app


class NewsData(models.Model):
    ticker = models.ForeignKey(Tickers, on_delete=models.CASCADE, related_name='news_data')
    published_date = models.DateTimeField()
    title = models.TextField()
    text = models.TextField(blank=True, null=True)
    url = models.URLField(max_length=500)
    site = models.CharField(max_length=255, blank=True, null=True)
    sentiment_classification = models.CharField(max_length=50)
    sentiment_score = models.DecimalField(max_digits=14, decimal_places=8)
    weighted_sentiment = models.DecimalField(max_digits=14, decimal_places=8, blank=True, null=True)
    keywords = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('ticker', 'published_date', 'url'),)
        indexes = [
            models.Index(fields=['ticker', 'published_date']),
            models.Index(fields=['sentiment_score']),
            GinIndex(fields=['keywords'], name='idx_news_data_keywords')
        ]
        db_table = 'Hybrid_Trading_Schema"."news_data'
        


