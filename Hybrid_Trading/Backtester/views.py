from django.shortcuts import render
from django.views.generic import FormView
from .forms import BacktestForm
from Hybrid_Trading.Backtester.Day_Trading_Backtester import DayTradingBacktester
import plotly.graph_objects as go  # For Plotly
from bokeh.plotting import figure  # For Bokeh
from bokeh.embed import components
import matplotlib.pyplot as plt  # For Charts (Matplotlib)
import pandas as pd
import io
from django.http import HttpResponse
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
import json

class BacktestView(FormView):
    template_name = 'run_backtest.html'
    form_class = BacktestForm

    async def run_backtest(self, user_input, session_id):
        """
        Async method to run the backtest using DayTradingBacktester
        and send real-time updates via WebSocket.
        """
        backtester = DayTradingBacktester(user_input, "/tmp")

        # Run the backtest asynchronously
        await backtester.run()

        # Fetch results
        results = backtester.export_results()

        # Send the final results to WebSocket clients
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'backtest_{session_id}',
            {
                'type': 'send_backtest_results',
                'message': json.dumps({'progress': 100, 'results': results})
            }
        )

        return results

    async def form_valid(self, form):
        # Extract form data
        user_input = {
            'ticker': form.cleaned_data['ticker'],
            'start_date': form.cleaned_data['start_date'],
            'end_date': form.cleaned_data['end_date'],
            'percentage_tickers': form.cleaned_data['percentage_tickers'],
            'granularity': form.cleaned_data['granularity'],
            'time_interval': form.cleaned_data['time_interval'],
            'strategy': form.cleaned_data['strategy']
        }

        # Get session ID for WebSocket tracking
        session_id = self.request.session.session_key

        # Start the backtest asynchronously and send results via WebSocket
        await self.run_backtest(user_input, session_id)

        # Render the page with the initial form
        return render(self.request, self.template_name, self.get_context_data(form=form))

    def generate_plotly_chart(self, results):
        fig = go.Figure()
        dates = [entry['date'] for entry in results['trade_log']]
        portfolio_values = [entry['portfolio_value'] for entry in results['trade_log']]

        fig.add_trace(go.Scatter(x=dates, y=portfolio_values, mode='lines', name='Portfolio Value'))
        fig.update_layout(title='Backtest Results', xaxis_title='Date', yaxis_title='Portfolio Value')
        return fig.to_html(full_html=False)

    def generate_bokeh_chart(self, results):
        p = figure(x_axis_type="datetime", title="Backtest Results")
        dates = [entry['date'] for entry in results['trade_log']]
        portfolio_values = [entry['portfolio_value'] for entry in results['trade_log']]

        p.line(dates, portfolio_values, legend_label="Portfolio Value", line_width=2)
        script, div = components(p)
        return script, div

    def generate_charts(self, results):
        dates = [entry['date'] for entry in results['trade_log']]
        portfolio_values = [entry['portfolio_value'] for entry in results['trade_log']]

        plt.figure(figsize=(10, 6))
        plt.plot(dates, portfolio_values, label='Portfolio Value', color='blue')
        plt.title('Backtest Results')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value')
        plt.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return buf.getvalue()

    def generate_csv(self, results):
        df = pd.DataFrame(results['trade_log'])
        return df.to_csv(index=False)

    def generate_excel(self, results):
        df = pd.DataFrame(results['trade_log'])
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf.getvalue()