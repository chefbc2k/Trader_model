from django.views.generic import TemplateView, View, FormView
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.db.models import Avg
from .models import NewsData  # Assuming you have a model called NewsData
from Hybrid_Trading.Analysis.News.news_classifier import NewsClassifier  # Corrected import path
from Hybrid_Trading.Data.Storage.CDS import CentralizedDataStorage
from Hybrid_Trading.Inputs.forms import ConfigurationForm  # Import your user input form

# Unified class-based view for rendering, analyzing sentiment, and classified news
class NewsAnalysisView(TemplateView):
    """
    A single view that:
    - Renders news data.
    - Analyzes sentiment via AJAX (optional).
    - Displays classified news based on user input.
    """
    template_name = 'analysis/news_analysis.html'
    form_class = ConfigurationForm

    def get_context_data(self, **kwargs):
        """
        Handles rendering of the news analysis page and form for user input.
        """
        context = super().get_context_data(**kwargs)

        # Retrieve news data for display
        news_data = NewsData.objects.all()
        context['news_data'] = news_data
        
        # Include the form for classified news
        context['form'] = self.form_class()

        return context

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for classified news analysis.
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            return self.process_classified_news(request, form)
        else:
            return self.form_invalid(form)

    def process_classified_news(self, request, form):
        """
        Processes classified news based on user inputs.
        """
        # Extract user inputs from the form
        ticker = form.cleaned_data['ticker']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        period = form.cleaned_data['period']
        interval = form.cleaned_data['interval']

        # Initialize the centralized data storage and news classifier
        storage = CentralizedDataStorage()
        user_input = form.cleaned_data
        classifier = NewsClassifier(user_input=user_input, ticker=ticker, start_date=start_date, 
                                    end_date=end_date, period=period, interval=interval, storage=storage)
        
        # Run the news classification process
        classifier.run_news_classification()
        
        # Retrieve the classified news and stock scores from storage
        news_data = storage.retrieve(ticker, "news_articles")
        stock_scores = storage.retrieve(ticker, "stock_scores")
        
        # Re-render the page with updated context
        context = self.get_context_data(form=form)
        context['ticker'] = ticker
        context['news_data'] = news_data
        context['stock_scores'] = stock_scores

        return render(request, self.template_name, context)

    def form_invalid(self, form):
        """
        Handles invalid form submissions.
        """
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests, including AJAX requests for sentiment analysis.
        """
        ticker = request.GET.get('ticker', None)
        if ticker:
            return self.analyze_sentiment(ticker)
        else:
            return self.render_to_response(self.get_context_data())

    def analyze_sentiment(self, ticker):
        """
        Analyzes the sentiment for a specific stock (AJAX handler).
        """
        news_data = get_object_or_404(NewsData, ticker=ticker)
        sentiment_avg = news_data.aggregate(Avg('sentiment_score'))
        return JsonResponse({'ticker': ticker, 'average_sentiment': sentiment_avg})