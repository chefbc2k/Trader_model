import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from Config.trading_constants import TCS
from Hybrid_Trading.Trading.Alpaca.alpaca import AlpacaAPI, PortfolioManager
from Config.utils import TradingDataWorkbook
from Hybrid_Trading.Inputs.user_input import UserInput

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='trading.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DayTradingLogic:
    def __init__(self, user_input: UserInput = None):
        logging.info("Initializing DayTradingLogic...")
        self.constants = TCS()  # Trading constants (e.g., position size, thresholds)
        self.alpaca_api = AlpacaAPI()  # Interface with the Alpaca API for trading
        self.portfolio_manager = PortfolioManager(user_input=user_input)  # Manages portfolio and trades
        self.workbook = TradingDataWorkbook()  # Handles saving trade results to a workbook
        self.user_input = user_input  # User input for customization

    def execute_trade(self, ticker: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"Executing trade for {ticker}...")

        # Extract the relevant decision information from signals
        dynamic_decision = signals.get('dynamic_decision', {})
        prediction_decision = signals.get('prediction_decision', {})
        instant_backtest_signals = signals.get('instant_backtest_signals', {})
        mrms_decision = signals.get('mrms_decision', {})
        vrs_decision = signals.get('vrs_decision', {})
        sentiment_score = signals.get('sentiment_score', 0)
        technical_indicator_final_signal = signals.get('technical_indicator_final_signal', 'Hold')
        insight_final_signal = signals.get('insight_final_signal', 'Hold')
        news_final_signal = signals.get('news_final_signal', 'Neutral')
        prophet_forecast_signal = signals.get('prophet_forecast_signal', 'NoForecast')
        current_price = signals.get('current_price', None)

        if current_price is None:
            logging.error(f"Current price not available for {ticker}")
            return None

        final_action = self.determine_final_action(
            dynamic_decision,
            prediction_decision,
            instant_backtest_signals,
            mrms_decision,
            vrs_decision,
            sentiment_score,
            technical_indicator_final_signal,
            insight_final_signal,
            news_final_signal,
            prophet_forecast_signal
        )
        
        quantity = self.calculate_position_size(float(self.alpaca_api.account.buying_power), current_price)
        logging.info(f"Calculated position size for {ticker}: {quantity}")

        trade_log = {
            'ticker': ticker,
            'dynamic_decision': dynamic_decision,
            'prediction_decision': prediction_decision,
            'instant_backtest_signals': instant_backtest_signals,
            'mrms_decision': mrms_decision,
            'vrs_decision': vrs_decision,
            'sentiment_score': sentiment_score,
            'technical_indicator_final_signal': technical_indicator_final_signal,
            'insight_final_signal': insight_final_signal,
            'news_final_signal': news_final_signal,
            'prophet_forecast_signal': prophet_forecast_signal,
            'final_action': final_action,
            'quantity': quantity,
            'current_price': current_price,
            'executed_at': datetime.now(),
        }

        if final_action == 'Buy' and self.is_eligible_for_trade(ticker, 'buy'):
            self.handle_order({'ticker': ticker, 'quantity': quantity, 'side': 'buy', 'current_price': current_price})
            trade_log['order_status'] = 'submitted'
        elif final_action == 'Sell' and self.is_eligible_for_trade(ticker, 'sell'):
            self.handle_order({'ticker': ticker, 'quantity': quantity, 'side': 'sell', 'current_price': current_price})
            trade_log['order_status'] = 'submitted'
        else:
            trade_log['order_status'] = 'not submitted'

        self.workbook.save_trade_result(ticker, trade_log)
        self.print_and_log_orders()

        return trade_log

    def determine_final_action(
        self,
        dynamic_decision: Dict[str, Any],
        prediction_decision: Dict[str, Any],
        instant_backtest_signals: Dict[str, Any],
        mrms_decision: Dict[str, Any],
        vrs_decision: Dict[str, Any],
        sentiment_score: float,
        technical_indicator_final_signal: str,
        insight_final_signal: str,
        news_final_signal: str,
        prophet_forecast_signal: str
    ) -> str:
        # Custom logic to determine the final action based on different strategy outputs
        actions = [
            dynamic_decision.get('action'),
            prediction_decision.get('action'),
            instant_backtest_signals.get('action'),
            mrms_decision.get('action'),
            vrs_decision.get('action'),
            technical_indicator_final_signal,
            insight_final_signal,
            news_final_signal,
            prophet_forecast_signal,
        ]

        # Logic to determine the final action
        if actions.count('Buy') > actions.count('Sell'):
            return 'Buy'
        elif actions.count('Sell') > actions.count('Buy'):
            return 'Sell'
        else:
            if sentiment_score > 0:
                return 'Buy'
            elif sentiment_score < 0:
                return 'Sell'
            else:
                return 'Hold'

    def calculate_position_size(self, buying_power: float, price: float) -> int:
        position_size = (buying_power * self.constants.POSITION_SIZE) / price
        return int(min(position_size, self.constants.MAX_INVESTMENT_PARTITION * buying_power / price))

    def handle_order(self, trade_details: Dict[str, Any]):
        ticker = trade_details.get('ticker')
        quantity = trade_details.get('quantity')
        side = trade_details.get('side')
        current_price = trade_details.get('current_price')

        logging.info(f"Handling order for {ticker}: {side} {quantity} at {current_price}")
        if self.alpaca_api.is_market_open():
            self.submit_order(trade_details)
        else:
            logging.info(f"Market is closed. Storing order for {ticker}: {side} {quantity} at {current_price}")
            self.portfolio_manager.pending_orders.append({
                'ticker': ticker,
                'quantity': quantity,
                'side': side,
                'price': current_price,
                'timestamp': datetime.now()
            })

    def submit_order(self, trade_details: Dict[str, Any]):
        ticker = trade_details.get('ticker')
        quantity = trade_details.get('quantity')
        side = trade_details.get('side')
        current_price = trade_details.get('current_price')

        try:
            self.alpaca_api.create_order({'ticker_symbol': ticker, 'quantity': quantity, 'side': side})
            logging.info(f"{side.capitalize()} order for {quantity} shares of {ticker} at {current_price} submitted.")
            self.portfolio_manager.record_trade(ticker, quantity, side, current_price)
        except Exception as e:
            logging.error(f"Error submitting {side} order for {ticker}: {e}")

    def is_eligible_for_trade(self, ticker: str, trade_type: str) -> bool:
        return self.portfolio_manager.is_eligible_for_trade(ticker, trade_type)

    def print_and_log_orders(self):
        logging.info("Current Trade Log:")
        for ticker, trades in self.portfolio_manager.trade_log.items():
            for trade in trades:
                logging.info(f"Ticker: {ticker}, Trade: {trade}")

        logging.info("Pending Orders:")
        for order in self.portfolio_manager.pending_orders:
            logging.info(f"Order: {order}")