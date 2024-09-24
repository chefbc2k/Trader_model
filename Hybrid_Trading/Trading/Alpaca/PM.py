import logging
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from tqdm import tqdm  # Import TQDM for progress monitoring
from Hybrid_Trading.Log.Logging_Master import LoggingMaster  # Ensure LoggingMaster is used for consistent logging

class PerformanceMetrics:
    def __init__(self):
        # Initialize LoggingMaster for this module
        self.logger = LoggingMaster("PerformanceMetrics").get_logger()
        self.logger.info("PerformanceMetrics module initialized.")

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.01) -> float:
        try:
            excess_returns = returns - risk_free_rate
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            self.logger.info(f"Calculated Sharpe Ratio: {sharpe_ratio}")
            return sharpe_ratio
        except Exception as e:
            self.logger.error(f"Failed to calculate Sharpe Ratio: {e}")
            return np.nan

    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.01) -> float:
        try:
            downside_risk = np.sqrt(((returns[returns < 0]) ** 2).mean())
            sortino_ratio = (returns.mean() - risk_free_rate) / downside_risk * np.sqrt(252)
            self.logger.info(f"Calculated Sortino Ratio: {sortino_ratio}")
            return sortino_ratio
        except Exception as e:
            self.logger.error(f"Failed to calculate Sortino Ratio: {e}")
            return np.nan

    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        try:
            cumulative_returns = (1 + returns).cumprod()
            drawdown = cumulative_returns.cummax() - cumulative_returns
            max_drawdown = drawdown.max()
            self.logger.info(f"Calculated Max Drawdown: {max_drawdown}")
            return max_drawdown
        except Exception as e:
            self.logger.error(f"Failed to calculate Max Drawdown: {e}")
            return np.nan

    def calculate_alpha_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> Dict[str, float]:
        try:
            cov_matrix = np.cov(returns, benchmark_returns)
            beta = cov_matrix[0, 1] / cov_matrix[1, 1]
            alpha = returns.mean() - beta * benchmark_returns.mean()
            self.logger.info(f"Calculated Alpha: {alpha}, Beta: {beta}")
            return {'alpha': alpha, 'beta': beta}
        except Exception as e:
            self.logger.error(f"Failed to calculate Alpha/Beta: {e}")
            return {'alpha': np.nan, 'beta': np.nan}

    def calculate_volatility(self, returns: pd.Series) -> float:
        try:
            volatility = returns.std() * np.sqrt(252)
            self.logger.info(f"Calculated Volatility: {volatility}")
            return volatility
        except Exception as e:
            self.logger.error(f"Failed to calculate Volatility: {e}")
            return np.nan

    def calculate_annualized_return(self, returns: pd.Series) -> float:
        try:
            compounded_growth = (1 + returns).prod()
            n_periods = returns.shape[0]
            annualized_return = compounded_growth ** (252 / n_periods) - 1
            self.logger.info(f"Calculated Annualized Return: {annualized_return}")
            return annualized_return
        except Exception as e:
            self.logger.error(f"Failed to calculate Annualized Return: {e}")
            return np.nan

    def calculate_metrics(self, trade_data: Dict[str, Any], benchmark_returns: pd.Series = None) -> Dict[str, Any]:
        metrics = {}
        returns = trade_data.get('returns')

        if returns is None or returns.empty:
            self.logger.error("No returns data found for metrics calculation.")
            return {}

        # Calculate each metric and handle potential failures
        metrics['sharpe_ratio'] = self.calculate_sharpe_ratio(returns)
        metrics['sortino_ratio'] = self.calculate_sortino_ratio(returns)
        metrics['max_drawdown'] = self.calculate_max_drawdown(returns)
        metrics['volatility'] = self.calculate_volatility(returns)
        metrics['annualized_return'] = self.calculate_annualized_return(returns)

        if benchmark_returns is not None:
            alpha_beta_metrics = self.calculate_alpha_beta(returns, benchmark_returns)
            metrics.update(alpha_beta_metrics)

        # Include other relevant metrics from trade_data
        metrics.update({
            'sentiment_score': trade_data.get('sentiment_score', np.nan),
            'weighted_sentiment': trade_data.get('weighted_sentiment', np.nan),
            'analyst_score': trade_data.get('analyst_score', np.nan),
            'dynamic_decision': trade_data.get('dynamic_decision', 'Hold'),
            'prediction_decision': trade_data.get('prediction_decision', 'Hold')
        })

        return metrics

    def process_batch(self, batch: List[Dict[str, Any]], benchmark_returns: pd.Series = None) -> Dict[str, Dict[str, Any]]:
        all_metrics = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.calculate_metrics, trade_data, benchmark_returns): trade_data['ticker'] for trade_data in batch}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Batch", unit="ticker"):
                ticker = futures[future]
                try:
                    result = future.result()
                    all_metrics[ticker] = result
                except Exception as e:
                    self.logger.error(f"Failed to process metrics for {ticker}: {e}")
                    all_metrics[ticker] = {}

        return all_metrics

    def export_to_excel(self, metrics: Dict[str, Dict[str, Any]], filepath: str):
        try:
            df = pd.DataFrame.from_dict(metrics, orient='index')
            df.to_excel(filepath, index=True)
            self.logger.info(f"Exported performance metrics to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to export metrics to Excel: {e}")