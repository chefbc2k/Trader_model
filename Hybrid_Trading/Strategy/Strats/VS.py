import logging
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List
from tqdm.asyncio import tqdm_asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValueSeekerStrategy:
    def __init__(self, tickers: List[str], user_input: Any, data: Dict[str, Any]):
        self.tickers = tickers
        self.data = data  # Data passed directly instead of pulling from centralized storage
        self.START_CAPITAL = user_input.get('start_capital', 1000)  # Initial capital from user input
        self.SLIPPAGE = user_input.get('slippage', 0.02)  # Slippage from user input

        # Thresholds for Financial Health
        self.THRESHOLDS = user_input.get('financial_thresholds', {
            'grossProfitMargin': 0.30,
            'operatingProfitMargin': 0.10,
            'netProfitMargin': 0.05,
            'debtEquityRatio': 1.0,
            'interestCoverage': 3.0,
            'currentRatio': 1.5,
            'quickRatio': 1.0,
            'priceEarningsRatio': 20,
            'priceBookValueRatio': 2.0,
            'priceSalesRatio': 3.0
        })

        # Sell thresholds
        self.SELL_THRESHOLDS = {
            'quickRatio': 1.0,
            'currentRatio': 1.2
        }

    def filter_stocks_by_financial_health(self) -> List[str]:
        filtered_stocks = []
        for ticker in self.tickers:
            ratios = self.data.get(ticker, {}).get('ratios')
            if not ratios:
                logger.warning(f"No financial data available for {ticker}")
                continue  # Skip if no ratios data

            latest_ratios = ratios[0]  # Get the latest available ratios
            meets_criteria = True
            for key, value in self.THRESHOLDS.items():
                if latest_ratios.get(key, 0) < value:
                    meets_criteria = False
                    break

            if meets_criteria:
                filtered_stocks.append(ticker)
                logger.info(f"{ticker} meets all financial health thresholds.")
            else:
                logger.info(f"{ticker} does not meet financial health thresholds.")

        return filtered_stocks

    def calculate_position_size(self, stock_price: float, capital: float) -> int:
        return int(capital // (stock_price * (1 + self.SLIPPAGE)))

    def generate_signals(self, latest_ratios: Dict[str, Any]) -> str:
        meets_buy_criteria = all(latest_ratios.get(key, 0) >= value for key, value in self.THRESHOLDS.items())
        quick_ratio = latest_ratios.get('quickRatio', 0)
        current_ratio = latest_ratios.get('currentRatio', 0)
        meets_sell_criteria = (quick_ratio < self.SELL_THRESHOLDS['quickRatio']) or (current_ratio < self.SELL_THRESHOLDS['currentRatio'])

        if meets_buy_criteria:
            logger.info(f"Buy signal generated based on financial ratios: {latest_ratios}")
            return "Buy"
        elif meets_sell_criteria:
            logger.info(f"Sell signal generated based on financial ratios: {latest_ratios}")
            return "Sell"
        else:
            logger.info(f"Hold signal generated based on financial ratios: {latest_ratios}")
            return "Hold"

    async def execute_trades(self) -> Dict[str, Any]:
        portfolio = {}
        capital = self.START_CAPITAL
        filtered_stocks = self.filter_stocks_by_financial_health()

        tasks = []
        for symbol in filtered_stocks:
            stock_price = self.data.get(symbol, {}).get('price')
            if not stock_price:
                continue  # Skip if no price data

            latest_ratios = self.data.get(symbol, {}).get('ratios', [{}])[0]
            signal = self.generate_signals(latest_ratios)

            tasks.append(self.handle_trade(symbol, stock_price, latest_ratios, signal, portfolio, capital))

        # Run the tasks concurrently using tqdm for progress tracking
        for task in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Processing Tickers", unit="ticker"):
            await task

        return portfolio, capital

    async def handle_trade(self, symbol, stock_price, latest_ratios, signal, portfolio, capital):
        if signal == "Buy":
            position_size = self.calculate_position_size(stock_price, capital)
            if position_size > 0:
                portfolio[symbol] = {
                    'position_size': position_size,
                    'purchase_price': stock_price,
                    'investment': position_size * stock_price * (1 + self.SLIPPAGE)
                }
                capital -= portfolio[symbol]['investment']
                logger.info(f"Bought {position_size} shares of {symbol} at ${stock_price:.2f} each.")
        elif signal == "Sell":
            if symbol in portfolio:
                sell_price = stock_price * portfolio[symbol]['position_size']
                capital += sell_price * (1 - self.SLIPPAGE)
                logger.info(f"Sold {portfolio[symbol]['position_size']} shares of {symbol} at ${stock_price:.2f} each.")
                del portfolio[symbol]
        elif signal == "Hold":
            logger.info(f"Holding position in {symbol}.")

    def generate_report(self, portfolio: Dict[str, Any], capital: float, period: str = "weekly") -> None:
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "portfolio_value": sum([stock['position_size'] * stock['purchase_price'] for stock in portfolio.values()]),
            "remaining_capital": capital,
            "holdings": portfolio
        }

        report_filename = f"{period}_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_filename, 'w') as report_file:
            report_file.write(str(report))

        logger.info(f"{period.capitalize()} report generated: {report_filename}")

    async def daily_report(self, portfolio: Dict[str, Any], capital: float) -> None:
        self.generate_report(portfolio, capital, period="daily")

    async def weekly_report(self, portfolio: Dict[str, Any], capital: float) -> None:
        self.generate_report(portfolio, capital, period="weekly")

    async def monthly_report(self, portfolio: Dict[str, Any], capital: float) -> None:
        self.generate_report(portfolio, capital, period="monthly")

    async def run(self) -> None:
        logger.info("Starting Value Seeker strategy...")

        # Execute trades
        portfolio, remaining_capital = await self.execute_trades()

        # Generate reports
        await self.daily_report(portfolio, remaining_capital)
        await self.weekly_report(portfolio, remaining_capital)
        await self.monthly_report(portfolio, remaining_capital)

        logger.info("Value Seeker strategy completed.")