from django.http import JsonResponse
from django.views.generic import TemplateView
from .forms import ForecasterForm  # Import the form for user input
from Hybrid_Trading.Forecaster.PF import TimeSeriesForecaster  # Import the relevant model or logic

class ForecastView(TemplateView):
    """A class-based view for handling forecast form input and processing."""
    template_name = 'forecast.html'

    def get_context_data(self, **kwargs):
        """Adds the form to the context for the template."""
        context = super().get_context_data(**kwargs)
        context['form'] = ForecasterForm()  # Add form to context on GET request
        return context

    def post(self, request, *args, **kwargs):
        """Handles POST request when form is submitted."""
        form = ForecasterForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            interval = form.cleaned_data['interval']
            period = form.cleaned_data['period']
            prediction_horizon = form.cleaned_data['prediction_horizon']
            fill_na_method = form.cleaned_data['fill_na_method']

            # Instantiate the TimeSeriesForecaster with the provided inputs
            forecaster = TimeSeriesForecaster(
                user_input={},
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                period=period,
                prediction_horizon=prediction_horizon,
                fill_na_method=fill_na_method
            )

            # Run the forecasting process
            forecaster.runPF()

            # Return a JSON response after the forecast is initiated
            return JsonResponse({"message": "Forecast initiated for ticker."})
        
        # Re-render the form with validation errors if form is not valid
        return self.render_to_response(self.get_context_data(form=form))