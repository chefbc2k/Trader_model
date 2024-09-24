import pandas as pd
from typing import Dict, Any, List
from Hybrid_Trading.Trading.TL.Trading_Logic import DayTradingLogic
from Hybrid_Trading.Log.Logging_Master import LoggingMaster
from Config.utils import TradingDataWorkbook
from tqdm.asyncio import tqdm_asyncio

class ExecuteTradesStage:
    def __init__(self, user_input):
        self.user_input = user_input
        self.logger = LoggingMaster("ExecuteTradesStage").get_logger()

    async def run(self, ticker: str, signals_data: Dict[str, Any]) -> bool:
        self.logger.info(f"Executing Trades for {ticker}")

        try:
            # Retrieve signals from the provided signals_data dictionary
            dynamic_signals = signals_data.get('dynamic_signals')
            prediction_signals = signals_data.get('prediction_signals')
            mrms_signals = signals_data.get('mrms_signals')
            vrs_signals = signals_data.get('vrs_signals')
            trading_signals = signals_data.get('trading_signals')
            value_seeker_signals = signals_data.get('value_seeker_signals')

            # Check if any signals are missing or not in DataFrame format
            if any(signal is None or not isinstance(signal, pd.DataFrame) for signal in [
                dynamic_signals, prediction_signals, mrms_signals, vrs_signals, trading_signals, value_seeker_signals
            ]):
                self.logger.warning(f"Missing or invalid signals for {ticker}. Skipping.")
                return False

            # Execute the trade logic
            trade_result = await self.execute_trade_logic(
                ticker,
                dynamic_signals=dynamic_signals,
                prediction_signals=prediction_signals,
                mrms_signals=mrms_signals,
                vrs_signals=vrs_signals,
                trading_signals=trading_signals,
                value_seeker_signals=value_seeker_signals
            )

            if trade_result:
                self.logger.info(f"Trade executed for {ticker}")
                await TradingDataWorkbook.instance().save_trade_result(ticker, trade_result)
                return True
            else:
                self.logger.error(f"Trade execution failed for {ticker}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing trades for {ticker}: {e}")
            return False

    async def execute_trade_logic(self, ticker: str, **signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the trading logic based on the provided signals.
        This method ensures all signals are correctly passed to the trading logic.
        """
        self.logger.info(f"Executing trade logic for {ticker}...")

        # Initialize the DayTradingLogic with the necessary signals and pass the user input
        day_trading_logic = DayTradingLogic(user_input=self.user_input)

        # Execute the trade using the provided signals
        trade_result = day_trading_logic.execute_trade(ticker=ticker, **signals)

        return trade_result

    async def process_tickers(self, tickers: List[str], signals_data: Dict[str, Any]):
        tasks = [self.run(ticker, signals_data[ticker]) for ticker in tickers]

        async for task in tqdm_asyncio.as_completed(tasks, total=len(tickers), desc="Executing Trades", unit="ticker"):
            await task