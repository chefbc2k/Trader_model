from django import forms

class ForecasterForm(forms.Form):
    ticker = forms.CharField(max_length=10, label='Stock Ticker')
    start_date = forms.DateField(label='Start Date')
    end_date = forms.DateField(label='End Date')
    interval = forms.ChoiceField(choices=[('daily', 'Daily'), ('weekly', 'Weekly')], label='Interval')
    period = forms.CharField(max_length=10, label='Period')
    prediction_horizon = forms.IntegerField(label='Prediction Horizon')
    fill_na_method = forms.ChoiceField(
        choices=[('mean', 'Mean'), ('median', 'Median'), ('zero', 'Zero'), ('interpolate', 'Interpolate'), ('drop', 'Drop')],
        label='NA Fill Method'
    )