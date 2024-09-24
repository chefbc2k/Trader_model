# strategy/views.py
from django.views.generic import TemplateView
from django.shortcuts import render
from  Hybrid_Trading.Strategy.forms import StrategyInputForm
from Hybrid_Trading.Pipeline.models import (
    PipelineBacktestResults, PipelineTradeSignals, PipelineGeneratedSignals, PipelinePerformanceMetrics
)

class StrategyResultsView(TemplateView):
    template_name = 'strategy_results.html'

    def get(self, request, *args, **kwargs):
        form = StrategyInputForm(request.GET or None)
        context = self.get_context_data(form=form)

        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            strategy_name = form.cleaned_data['strategy_name']
            
            # Retrieve data from the database
            try:
                backtest_results = PipelineBacktestResults.objects.filter(ticker__ticker=ticker).latest('created_at')
                trade_signals = PipelineTradeSignals.objects.filter(ticker__ticker=ticker).latest('created_at')
                generated_signals = PipelineGeneratedSignals.objects.filter(ticker__ticker=ticker).latest('created_at')
                performance_metrics = PipelinePerformanceMetrics.objects.filter(ticker__ticker=ticker).latest('created_at')

                # Add the retrieved data to the context
                context.update({
                    'ticker': ticker,
                    'strategy_name': strategy_name,
                    'action': generated_signals.dynamic_signals.get('action', 'Hold'),
                    'reason': generated_signals.dynamic_signals.get('reason', 'No reason provided'),
                    'current_price': backtest_results.real_time_data.get('last_sale_price', None),
                    'predicted_price': backtest_results.prophet_forecast.get('yhat', None),
                    'rsi': backtest_results.technical_indicators.get('rsi', None),
                    'moving_average': backtest_results.technical_indicators.get('sma', None),
                    'bollinger_upper': backtest_results.technical_indicators.get('bollinger_upper', None),
                    'bollinger_lower': backtest_results.technical_indicators.get('bollinger_lower', None),
                    'stop_loss_level': trade_signals.dynamic_signals.get('stop_loss', None),
                    'take_profit_level': trade_signals.dynamic_signals.get('take_profit', None),
                    'sentiment_score': generated_signals.dynamic_signals.get('sentiment_score', None),
                    'past_trade_buy_price': trade_signals.dynamic_signals.get('buy_price', None),
                    'past_trade_buy_date': trade_signals.dynamic_signals.get('buy_date', None),
                    'past_trade_sell_price': trade_signals.dynamic_signals.get('sell_price', None),
                    'past_trade_sell_date': trade_signals.dynamic_signals.get('sell_date', None),
                    'signal_1': generated_signals.dynamic_signals.get('signal_1', None),
                    'signal_1_price': generated_signals.dynamic_signals.get('signal_1_price', None),
                    'signal_2': generated_signals.dynamic_signals.get('signal_2', None),
                    'signal_2_price': generated_signals.dynamic_signals.get('signal_2_price', None),
                    'current_volume': backtest_results.real_time_data.get('volume', None),
                    'bid_ask_spread': backtest_results.real_time_data.get('bid_ask_spread', None),
                    'sp500_performance': performance_metrics.sharpe_ratio,  # Example of metric
                    'strategy_performance': performance_metrics.annualized_return,  # Example of performance metric
                })

            except PipelineBacktestResults.DoesNotExist:
                context['error'] = 'No results found for the selected strategy and ticker.'

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form')
        return context