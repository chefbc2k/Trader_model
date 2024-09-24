from django import forms

class StrategyInputForm(forms.Form):
    ticker = forms.CharField(max_length=10, required=True, label="Ticker Symbol")
    start_date = forms.DateField(required=False, label="Start Date")
    end_date = forms.DateField(required=False, label="End Date")
    sentiment_score = forms.FloatField(required=False, label="Sentiment Score")
    period = forms.CharField(max_length=10, required=False, label="Period")
    target_column = forms.CharField(max_length=50, required=False, label="Target Column", initial="close")
    percentage = forms.IntegerField(required=False, label="Percentage of Tickers to Process", min_value=1, max_value=100)
    interval = forms.CharField(max_length=10, required=False, label="Interval", initial="1d")
    handle_missing_values = forms.ChoiceField(
        choices=[('drop', 'Drop'), ('fill', 'Fill'), ('interpolate', 'Interpolate')],
        required=False, label="Handle Missing Values"
    )
    fillna_method = forms.ChoiceField(
        choices=[('mean', 'Mean'), ('median', 'Median'), ('zero', 'Zero')],
        required=False, label="Fill NA Method"
    )
    sentiment_type = forms.ChoiceField(
        choices=[('bullish', 'Bullish'), ('bearish', 'Bearish'), ('neutral', 'Neutral')],
        required=False, label="Sentiment Type"
    )
    market_cap_filter = forms.ChoiceField(
        choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large'), ('all', 'All')],
        required=False, label="Market Cap Filter"
    )

    # Fields for more strategies can be added here based on requirements