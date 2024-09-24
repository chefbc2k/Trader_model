import logging
from typing import Dict, Any
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)

class TradingSignalAggregator:
    def __init__(self, ticker: str):
        self.ticker = ticker

        # Lazy import of constants
        from Config.trading_constants import TCS
        self.constants = TCS()

        logging.info(f"Initialized TradingSignalAggregator for ticker {ticker}")

    def gather_signals(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gathers signals from the analysis result and determines the final signal.
        """
        logging.info(f"Gathering final signal for ticker {self.ticker}")

        try:
            # Retrieve the final signal from the analysis result
            ticker_analysis = analysis_result.get(self.ticker, {})
            final_signal = ticker_analysis.get('final_signal', None)

            if final_signal is None:
                logging.error(f"Missing final signal for ticker {self.ticker}. No trade executed.")
                return {}

            signal_counts = ticker_analysis.get('signal_counts', {})

            logging.info(f"Final signal for ticker {self.ticker}: {final_signal}")

            return {
                'Ticker': self.ticker,
                'FinalSignal': final_signal,
                'SignalCounts': signal_counts
            }
        except Exception as e:
            logging.error(f"Error gathering signals for {self.ticker}: {e}")
            return {}

    def output_signals(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Outputs the gathered signals for further processing.
        """
        logging.info(f"Outputting signals for ticker {self.ticker}")
        return self.gather_signals(analysis_result)

    def export_signals_to_excel(self, signals: Dict[str, Any], filepath: str):
        """
        Exports the trading signals to an Excel file.
        """
        if not signals:
            logging.error("No signals to export")
            return

        logging.info(f"Exporting signals to {filepath}")
        signals_df = pd.DataFrame([signals])
        with pd.ExcelWriter(filepath) as writer:
            signals_df.to_excel(writer, sheet_name='Trading Signals', index=False)
            logging.info(f"Signals successfully exported to {filepath}")