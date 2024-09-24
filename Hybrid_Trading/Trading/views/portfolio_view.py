from django.views.generic import TemplateView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from Hybrid_Trading.Trading.Alpaca.alpaca import PortfolioManager  # Assuming this is where PortfolioManager is implemented
from django.http import JsonResponse

class PortfolioView(TemplateView):
    template_name = 'portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Simulate or replace with actual user inputs as necessary
        user_input = {
            'STARTING_ACCOUNT_VALUE': 100000  # Initial balance, can be fetched dynamically if needed
        }

        # Initialize PortfolioManager
        portfolio_manager = PortfolioManager(user_input)

        # Read the portfolio data (replace 'all' with actual method or logic as necessary)
        portfolio_manager.read_json('all')  # Assumes 'all' fetches purchased and sold data

        # Refresh account balance after actions
        account_data = portfolio_manager.refresh_account_balance()

        # Pass the portfolio data to the context
        context['purchased'] = portfolio_manager.purchased
        context['sold'] = portfolio_manager.sold
        context['transaction_history'] = portfolio_manager.transaction_history
        context['account_value'] = account_data['account_value']
        context['buying_power'] = account_data['buying_power']

        return context

    def websocket_receive(self, message):
        """
        Handle WebSocket messages for buy/sell actions.
        """
        # Parse message content (this would be the form data sent via WebSocket)
        action = message['action']
        ticker = message['ticker']
        quantity = int(message['quantity'])
        price = float(message['price'])

        # Initialize PortfolioManager with user inputs (e.g., starting account value)
        user_input = {
            'STARTING_ACCOUNT_VALUE': 100000  # This could be dynamically set based on session/user
        }
        portfolio_manager = PortfolioManager(user_input)

        # Prepare trade details
        trade_details = {
            'ticker_symbol': ticker,
            'quantity': quantity,
            'price': price
        }

        # Execute the trade based on the action (buy or sell)
        if action == 'buy':
            portfolio_manager.buy_stock(trade_details)
            response_message = f"Successfully bought {quantity} shares of {ticker} at {price}."
        elif action == 'sell':
            portfolio_manager.sell_stock(trade_details)
            response_message = f"Successfully sold {quantity} shares of {ticker} at {price}."
        else:
            response_message = "Invalid action."

        # Send the response back through WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'portfolio_group',
            {
                'type': 'portfolio_message',
                'message': response_message
            }
        )

        return JsonResponse({'status': 'success', 'message': response_message})