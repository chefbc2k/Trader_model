import os
import logging
import threading
from datetime import datetime
from typing import Any, Dict
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# Configure logging using the new logging master setup
logging.basicConfig(
    filename='trading.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Alpaca API keys and URL
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")

class AlpacaAPI:
    def __init__(self):
        self.api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)
        self.account = self.api.get_account()
        logging.info(f"Account Status: {self.account.status}")

    def create_order(self, trade_details: Dict[str, Any]):
        ticker_symbol = trade_details.get('ticker_symbol')
        quantity = trade_details.get('quantity')
        side = trade_details.get('side', 'buy')
        try:
            self.api.submit_order(
                symbol=ticker_symbol,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day'
            )
            logging.info(f"{side.capitalize()} order created for {quantity} shares of {ticker_symbol}")
        except Exception as e:
            logging.error(f"Error creating {side} order for {ticker_symbol}: {e}")

    def close_position(self, ticker_details: Dict[str, Any]):
        ticker_symbol = ticker_details.get('ticker_symbol')
        try:
            self.api.close_position(ticker_symbol)
            logging.info(f"Closed position for {ticker_symbol}")
        except Exception as e:
            logging.error(f"Error closing position for {ticker_symbol}: {e}")

    def close_all_positions(self):
        try:
            self.api.close_all_positions()
            self.api.cancel_all_orders()
            logging.info("Closed all positions and canceled all orders")
        except Exception as e:
            logging.error(f"Error closing all positions: {e}")

    def get_positions(self) -> Dict[str, Any]:
        try:
            positions = self.api.list_positions()
            return {position.symbol: position for position in positions}
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return {}

    def get_positions_tickers(self) -> Dict[str, Any]:
        try:
            positions = self.api.list_positions()
            return {position.symbol: position.symbol for position in positions}
        except Exception as e:
            logging.error(f"Error getting positions tickers: {e}")
            return {}

class PortfolioManager:
    def __init__(self, user_input: Dict[str, Any]):
        self.purchased = {}
        self.sold = {}
        self.transaction_history = []
        self.lock = threading.Lock()
        self.user_input = user_input  # Include user inputs for start date, end date, etc.

   

    def read_json(self, filename: str):
        with self.lock:
            if filename in ['all', 'purchased']:
                if not os.path.exists('purchased.json'):
                    with open('purchased.json', "w") as file:
                        json.dump({}, file)  # Create an empty JSON file if it doesn't exist
                with open('purchased.json', "r+") as file:
                    self.purchased = json.load(file)
            if filename in ['all', 'sold']:
                if not os.path.exists('sold.json'):
                    with open('sold.json', "w") as file:
                        json.dump({}, file)  # Create an empty JSON file if it doesn't exist
                with open('sold.json', "r+") as file:
                    self.sold = json.load(file)

    def update_json(self, data_type: str):
        with self.lock:
            if data_type == 'purchased':
                with open('purchased.json', "w") as file:
                    json.dump(self.purchased, file, indent=4)
            elif data_type == 'sold':
                with open('sold.json', "w") as file:
                    json.dump(self.sold, file, indent=4)

    def buy_stock(self, stock_details: Dict[str, Any]):
        ticker_symbol = stock_details.get('ticker_symbol')
        quantity = stock_details.get('quantity')
        price = stock_details.get('price')
        with self.lock:
            if ticker_symbol not in self.purchased:
                self.purchased[ticker_symbol] = {
                    'Quantity': quantity,
                    'Close': price,
                    'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                logging.info(f"Bought {quantity} shares of {ticker_symbol} at {price}")
                self.transaction_history.append({
                    "type": "buy",
                    "symbol": ticker_symbol,
                    "quantity": quantity,
                    "price": price,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.update_json('purchased')

    def sell_stock(self, stock_details: Dict[str, Any]):
        ticker_symbol = stock_details.get('ticker_symbol')
        quantity = stock_details.get('quantity')
        price = stock_details.get('price')
        with self.lock:
            if ticker_symbol in self.purchased:
                purchased_info = self.purchased.pop(ticker_symbol)
                self.sold[ticker_symbol] = {
                    'Quantity': quantity,
                    'Close': price,
                    'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                logging.info(f"Sold {quantity} shares of {ticker_symbol} at {price}")
                self.transaction_history.append({
                    "type": "sell",
                    "symbol": ticker_symbol,
                    "quantity": quantity,
                    "price": price,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.update_json('purchased')
                self.update_json('sold')

    def refresh_account_balance(self) -> Dict[str, float]:
        with self.lock:
            self.read_json('purchased')
            self.read_json('sold')

            buying_power = self.user_input['STARTING_ACCOUNT_VALUE ']  # Use user input for initial balance
            account_value = self.user_input['STARTING_ACCOUNT_VALUE ']

            for ticker_symbol, stock in self.purchased.items():
                current_price = stock['Close']
                purchased_quantity = stock['Quantity']
                account_value += current_price * purchased_quantity
                buying_power -= current_price * purchased_quantity

            for ticker_symbol, stock in self.sold.items():
                sold_price = stock['Close']
                sold_quantity = stock['Quantity']
                account_value += sold_price * sold_quantity
                buying_power += sold_price * sold_quantity

            return {'buying_power': buying_power, 'account_value': account_value}

    def execute_parallel_trades(self, trades: list):
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(self.execute_trade, trade) for trade in trades]
            for future in as_completed(futures):
                try:
                    future.result()  # Retrieve the result to catch exceptions
                except Exception as e:
                    logging.error(f"Error executing trade: {e}")

    def execute_trade(self, trade: Dict[str, Any]):
        ticker = trade.get('ticker')
        action = trade.get('action')
        quantity = trade.get('quantity')
        price = trade.get('price')
        
        if action == 'buy':
            self.buy_stock({'ticker_symbol': ticker, 'quantity': quantity, 'price': price})
        elif action == 'sell':
            self.sell_stock({'ticker_symbol': ticker, 'quantity': quantity, 'price': price})