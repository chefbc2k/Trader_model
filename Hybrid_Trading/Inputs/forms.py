from django import forms

class ConfigurationForm(forms.Form):
    MODES = [
        ('full_run', 'Full Run'),
        ('backtester', 'Backtester'),
        ('day_trader', 'Day Trader'),
        ('sentiment_analysis', 'Sentiment Analysis'),
    ]

    # Common fields across all modes with placeholders
    mode = forms.ChoiceField(choices=MODES, label="Select Mode", widget=forms.Select(attrs={'placeholder': 'Select a mode'}))
    start_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}), label="Start Date")
    end_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}), label="End Date")
    
    # General fields that will always be available for different modes
    percentage = forms.ChoiceField(
        choices=[
            (1, '1%'), (5, '5%'), (10, '10%'), (25, '25%'), (50, '50%'), 
            (75, '75%'), (100, '100%')
        ], 
        label="Percentage", widget=forms.Select(attrs={'placeholder': 'Select percentage'})
    )
    interval = forms.ChoiceField(
        choices=[
            ('1min', '1 Minute'), ('5min', '5 Minutes'), ('15min', '15 Minutes'),
            ('30min', '30 Minutes'), ('60min', '1 Hour'), ('1d', '1 Day')
        ], 
        label="Interval", required=False, widget=forms.Select(attrs={'placeholder': 'Select interval'})
    )
    period = forms.ChoiceField(
        choices=[('D', 'Daily'), ('W', 'Weekly'), ('H', 'Hourly')],
        label="Period", required=False, widget=forms.Select(attrs={'placeholder': 'Select period'})
    )
    fillna_method = forms.ChoiceField(
        choices=[('mean', 'Mean'), ('median', 'Median'), ('zero', 'Zero')],
        label="Fill NA Method", required=False, widget=forms.Select(attrs={'placeholder': 'Select fill method'})
    )
    sentiment_type = forms.ChoiceField(
        choices=[('bullish', 'Bullish'), ('bearish', 'Bearish'), ('neutral', 'Neutral')],
        label="Sentiment Type", required=False, widget=forms.Select(attrs={'placeholder': 'Select sentiment type'})
    )

    # Fields specific to 'sentiment_analysis' mode
    sentiment_score_threshold = forms.FloatField(
        label="Sentiment Score Threshold", required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Select threshold (0.0 - 5.0)', 'min': 0, 'max': 5})
    )
    market_cap_filter = forms.ChoiceField(
        choices=[('small', 'Small Cap'), ('medium', 'Medium Cap'), ('large', 'Large Cap'), ('all', 'All')],
        label="Market Cap Filter", required=False, widget=forms.Select(attrs={'placeholder': 'Select market cap'})
    )
    sector = forms.ChoiceField(
        choices=[('technology', 'Technology'), ('finance', 'Finance'), ('energy', 'Energy'), ('healthcare', 'Healthcare')],
        label="Sector", required=False, widget=forms.Select(attrs={'placeholder': 'Select sector'})
    )
    region = forms.ChoiceField(
        choices=[('USA', 'USA'), ('Europe', 'Europe'), ('Asia', 'Asia'), ('Global', 'Global')],
        label="Region", required=False, widget=forms.Select(attrs={'placeholder': 'Select region'})
    )
    time_of_day = forms.ChoiceField(
        choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('evening', 'Evening')],
        label="Time of Day", required=False, widget=forms.Select(attrs={'placeholder': 'Select time of day'})
    )
    analyst_consensus = forms.ChoiceField(
        choices=[('buy', 'Buy'), ('hold', 'Hold'), ('sell', 'Sell')],
        label="Analyst Consensus", required=False, widget=forms.Select(attrs={'placeholder': 'Select consensus'})
    )
    sentiment_momentum = forms.ChoiceField(
        choices=[('increasing', 'Increasing'), ('decreasing', 'Decreasing'), ('steady', 'Steady')],
        label="Sentiment Momentum", required=False, widget=forms.Select(attrs={'placeholder': 'Select momentum'})
    )

    def __init__(self, *args, **kwargs):
        super(ConfigurationForm, self).__init__(*args, **kwargs)
        # No need to dynamically load configurations, all options are hardcoded here
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data