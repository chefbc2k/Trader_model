from django import forms
from django.core.exceptions import ValidationError
from datetime import date

# Defining choices for the fields
GRANULARITY_CHOICES = [
    ('', 'Choose Data Granularity'),  # Placeholder
    ('daily', 'Daily Data'),
    ('weekly', 'Weekly Data'),
    ('monthly', 'Monthly Data'),
    ('1min', '1 Minute Data'),
    ('5min', '5 Minute Data')
]

STRATEGY_CHOICES = [
    ('', 'Choose Strategy'),  # Placeholder
    ('strategy1', 'Mean Reversion'),
    ('strategy2', 'Momentum'),
    ('strategy3', 'Volatility Reversion'),
    ('strategy4', 'Value Seeking'),
    ('strategy5', 'Prediction-based'),
    ('strategy6', 'Dynamic Strategy')
]

# Parameters mapped to each strategy
STRATEGY_PARAMETERS_CHOICES = {
    'strategy1': [
        ('', 'Choose Parameter'),  # Placeholder
        ('param1', 'Mean Reversion Lookback Period'),
        ('param2', 'Mean Reversion Entry Threshold'),
        ('param3', 'Mean Reversion Exit Threshold')
    ],
    'strategy2': [
        ('', 'Choose Parameter'),  # Placeholder
        ('param1', 'Momentum Window Size'),
        ('param2', 'Momentum Signal Smoothing'),
        ('param3', 'Momentum Confirmation Period')
    ],
    'strategy3': [
        ('', 'Choose Parameter'),  # Placeholder
        ('param1', 'Volatility Lookback Period'),
        ('param2', 'Bollinger Bands Width'),
        ('param3', 'RSI Overbought Level')
    ],
    'strategy4': [
        ('', 'Choose Parameter'),  # Placeholder
        ('param1', 'Value Seeking PE Ratio'),
        ('param2', 'Price to Book Ratio'),
        ('param3', 'Dividend Yield Threshold')
    ],
    'strategy5': [
        ('', 'Choose Parameter'),  # Placeholder
        ('param1', 'Prediction Model Type'),
        ('param2', 'Forecast Window'),
        ('param3', 'Confidence Interval')
    ],
    'strategy6': [
        ('', 'Choose Parameter'),  # Placeholder
        ('param1', 'Dynamic Indicator 1'),
        ('param2', 'Dynamic Indicator 2'),
        ('param3', 'Dynamic Momentum Factor')
    ]
}

OUTPUT_CHOICES = [
    ('', 'Choose Output Option'),  # Placeholder
    ('plotly', 'Plotly Interactive Chart'),
    ('bokeh', 'Bokeh Interactive Chart'),
    ('charts', 'Matplotlib/Altair Chart'),
    ('csv', 'CSV Export'),
    ('excel', 'Excel Export')
]

RISK_MANAGEMENT_CHOICES = [
    ('stop_loss', 'Stop Loss'),
    ('take_profit', 'Take Profit'),
    ('trailing_stop', 'Trailing Stop'),
    ('position_sizing', 'Position Sizing')
]

BENCHMARK_CHOICES = [
    ('', 'Choose Benchmark'),  # Placeholder
    ('sp500', 'S&P 500'),
    ('nasdaq', 'NASDAQ'),
    ('djia', 'Dow Jones'),
    ('custom', 'Custom Benchmark')
]

BENCHMARK_TYPE_CHOICES = [
    ('', 'Choose Benchmark Type'),  # Placeholder
    ('daily', 'Daily Benchmarking'),
    ('weekly', 'Weekly Benchmarking'),
    ('monthly', 'Monthly Benchmarking')
]

class BacktestForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.SelectDateWidget(
            empty_label=("Choose Year", "Choose Month", "Choose Day"),
            attrs={'placeholder': 'Select Start Date'}
        )
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.SelectDateWidget(
            empty_label=("Choose Year", "Choose Month", "Choose Day"),
            attrs={'placeholder': 'Select End Date'}
        )
    )
    percentage_tickers = forms.ChoiceField(
        choices=[('', 'Choose Percentage')] + [
            (1, '1% of Tickers'), (10, '10% of Tickers'), 
            (30, '30% of Tickers'), (50, '50% of Tickers'), 
            (70, '70% of Tickers'), (100, '100% of Tickers')
        ],
        label="Percentage of Tickers to Backtest",
        widget=forms.Select(attrs={'placeholder': 'Choose Percentage of Tickers'})
    )

    # Granularity and Interval Selection
    granularity = forms.ChoiceField(
        choices=GRANULARITY_CHOICES,
        label="Data Granularity",
        widget=forms.Select(attrs={'placeholder': 'Select Data Granularity'})
    )
    time_interval = forms.ChoiceField(
        choices=GRANULARITY_CHOICES,
        label="Time Series Interval",
        widget=forms.Select(attrs={'placeholder': 'Select Time Interval'})
    )

    # Strategy Selection and Parameters
    strategy = forms.ChoiceField(
        choices=STRATEGY_CHOICES,
        label="Trading Strategy",
        widget=forms.Select(attrs={'placeholder': 'Choose a Strategy'})
    )
    strategy_parameters = forms.ChoiceField(
        label="Strategy Parameters",
        required=False,
        choices=[],  # Initially empty, populated dynamically via JavaScript
        widget=forms.Select(attrs={'placeholder': 'Select Strategy Parameters'})
    )

    # Output Options
    output_options = forms.ChoiceField(
        choices=OUTPUT_CHOICES,
        label="Output Options",
        widget=forms.Select(attrs={'placeholder': 'Select Output Format'})
    )

    # Risk Management Parameters
    risk_management = forms.MultipleChoiceField(
        choices=RISK_MANAGEMENT_CHOICES,
        label="Risk Management Settings",
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    # Benchmark Selection
    benchmark = forms.ChoiceField(
        choices=BENCHMARK_CHOICES,
        label="Benchmark Index",
        widget=forms.Select(attrs={'placeholder': 'Select Benchmark'})
    )
    benchmark_type = forms.ChoiceField(
        choices=BENCHMARK_TYPE_CHOICES,
        label="Benchmark Period",
        widget=forms.Select(attrs={'placeholder': 'Select Benchmark Time Period'})
    )

    # Validations
    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if end_date and start_date and end_date < start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        granularity = cleaned_data.get('granularity')
        output_option = cleaned_data.get('output_options')
        strategy = cleaned_data.get('strategy')
        risk_management = cleaned_data.get('risk_management')

        # Validation: Prevent bulk export for minute-level data
        if granularity in ['1min', '5min'] and output_option in ['csv', 'excel']:
            self.add_error('output_options', 'CSV/Excel export is not allowed for minute-level data.')

        # Ensure valid strategy and risk management combinations
        if strategy == 'strategy2' and 'trailing_stop' in risk_management:
            self.add_error('risk_management', 'Trailing Stop is incompatible with the Momentum strategy.')

        if strategy == 'strategy4' and granularity == '1min':
            self.add_error('granularity', 'Value Seeking strategy is unsuitable for minute-level data.')

        return cleaned_data