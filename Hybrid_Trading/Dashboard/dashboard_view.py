from django.views.generic import TemplateView
from django.utils import timezone
from django.db import connection
import plotly.graph_objs as go
import pandas as pd
from Hybrid_Trading.Model_Trainer.models import ModelEvaluation, ModelPrediction, TradeSignal
from Hybrid_Trading.Backtester.models import BacktestResults, BacktestResultsTradeLogs
from Hybrid_Trading.Trading.models import PerformanceMetrics, TradeLogs, Signals
import logging

# Set up logging
logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch the dynamic data from the three model sets (ModelTrainer, Trading, Backtester)
        model_performance_data = self.get_model_performance_data()
        trade_signal_data = self.get_trade_signal_data()
        backtest_results = self.get_backtest_results()
        trade_logs = self.get_trade_logs()  # Added trade logs
        signals = self.get_signals()  # Added signals
        performance_metrics = self.get_performance_metrics()  # Added performance metrics

        # Dynamically cross-reference data and aggregate insights
        cross_referenced_data = self.get_cross_referenced_data(
            model_performance_data,
            trade_signal_data,
            backtest_results,
            performance_metrics
        )

        # Convert DataFrames to HTML tables or JSON strings if necessary
        context['model_performance_data_html'] = model_performance_data.to_html(classes='table table-striped') if not model_performance_data.empty else "<p>No Model Performance Data Available.</p>"
        context['trade_signal_data_html'] = trade_signal_data.to_html(classes='table table-striped') if not trade_signal_data.empty else "<p>No Trade Signal Data Available.</p>"
        context['backtest_results_html'] = backtest_results.to_html(classes='table table-striped') if not backtest_results.empty else "<p>No Backtest Results Available.</p>"
        context['trade_logs_html'] = trade_logs.to_html(classes='table table-striped') if not trade_logs.empty else "<p>No Trade Logs Available.</p>"
        context['signals_html'] = signals.to_html(classes='table table-striped') if not signals.empty else "<p>No Signals Available.</p>"
        context['performance_metrics_html'] = performance_metrics.to_html(classes='table table-striped') if not performance_metrics.empty else "<p>No Performance Metrics Available.</p>"
        context['cross_referenced_data_html'] = cross_referenced_data.to_html(classes='table table-striped') if not cross_referenced_data.empty else "<p>No Cross Referenced Data Available.</p>"

        # Charts for Predictions vs Actuals, Performance Metrics, etc.
        context['predictions_vs_actuals_chart'] = self.create_predictions_vs_actuals_chart()
        context['performance_metrics_chart'] = self.create_performance_metrics_chart(model_performance_data)
        context['backtest_trade_logs_chart'] = self.create_backtest_trade_logs_chart()

        return context

    def table_exists(self, table_name):
        """
        Check if a table exists in the database.
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, [table_name])
            return cursor.fetchone()[0]

    # Fetch data from ModelTrainer.Models (ModelEvaluation)
    def get_model_performance_data(self):
        if self.table_exists('model_evaluation'):
            model_evaluations = ModelEvaluation.objects.filter(
                timestamp__lte=timezone.now()
            ).values(
                'mae',
                'rmse',
                'mape',
                'r2',
                'evaluation_set',
                'model_training__user_input__datasource__ticker__ticker'  # Corrected lookup
            )
            df = pd.DataFrame(model_evaluations)
            print("Model Performance Data Columns:", df.columns)  # For debugging
            print("Model Performance Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("ModelEvaluation table does not exist.")
            return pd.DataFrame()

    def get_trade_signal_data(self):
        if self.table_exists('trade_signal'):
            trade_signals = TradeSignal.objects.filter(
                signal_date__lte=timezone.now()
            ).values('ticker__ticker', 'signal', 'signal_date')
            df = pd.DataFrame(trade_signals)
            print("Trade Signal Data Columns:", df.columns)  # For debugging
            print("Trade Signal Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("TradeSignal table does not exist.")
            return pd.DataFrame()

    # Fetch backtest results from BackTester.Models
    def get_backtest_results(self):
        if self.table_exists('backtest_results'):
            backtest_results = BacktestResults.objects.filter(
                backtest_date__lte=timezone.now()
            ).values('ticker__ticker', 'final_portfolio_value', 'trade_log', 'backtest_date')
            df = pd.DataFrame(backtest_results)
            print("Backtest Results Data Columns:", df.columns)  # For debugging
            print("Backtest Results Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("BacktestResults table does not exist.")
            return pd.DataFrame()

    # Fetch trade logs from Trading.Models (TradeLogs)
    def get_trade_logs(self):
        if self.table_exists('trade_logs'):
            trade_logs = TradeLogs.objects.filter(
                date__lte=timezone.now()
            ).values('ticker__ticker', 'action', 'quantity', 'price', 'date', 'portfolio_value')
            df = pd.DataFrame(trade_logs)
            print("Trade Logs Data Columns:", df.columns)  # For debugging
            print("Trade Logs Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("TradeLogs table does not exist.")
            return pd.DataFrame()

    # Fetch signals from Trading.Models (Signals)
    def get_signals(self):
        if self.table_exists('signals'):
            signals = Signals.objects.filter(
                date__lte=timezone.now()
            ).values('ticker__ticker', 'dynamic_decision', 'final_signal', 'action', 'created_at')
            df = pd.DataFrame(signals)
            print("Signals Data Columns:", df.columns)  # For debugging
            print("Signals Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("Signals table does not exist.")
            return pd.DataFrame()

    # Fetch performance metrics from Trading.Models (PerformanceMetrics)
    def get_performance_metrics(self):
        if self.table_exists('performance_metrics'):
            performance_metrics = PerformanceMetrics.objects.filter(
                calculated_at__lte=timezone.now()
            ).values(
                'ticker__ticker',
                'sharpe_ratio',
                'sortino_ratio',
                'max_drawdown',
                'volatility',
                'annualized_return'
            )
            df = pd.DataFrame(performance_metrics)
            print("Performance Metrics Data Columns:", df.columns)  # For debugging
            print("Performance Metrics Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("PerformanceMetrics table does not exist.")
            return pd.DataFrame()

    # Dynamically cross-reference data across models
    def get_cross_referenced_data(self, model_performance_data, trade_signal_data, backtest_data, performance_metrics):
        # Rename 'model_training__user_input__datasource__ticker__ticker' to 'ticker__ticker' for consistency
        ticker_column = 'model_training__user_input__datasource__ticker__ticker'
        if ticker_column in model_performance_data.columns:
            model_performance_data.rename(
                columns={ticker_column: 'ticker__ticker'},
                inplace=True
            )
            print(f"Renamed '{ticker_column}' to 'ticker__ticker' in model_performance_data.")
        else:
            logger.error(f"'{ticker_column}' column not found in model_performance_data.")
            return pd.DataFrame()

        # Verify 'ticker__ticker' exists in trade_signal_data
        if 'ticker__ticker' not in trade_signal_data.columns:
            logger.error("'ticker__ticker' column not found in trade_signal_data.")
            return pd.DataFrame()

        # Debugging: Print head of DataFrames
        print("Model Performance Data Head:\n", model_performance_data.head())
        print("Trade Signal Data Head:\n", trade_signal_data.head())

        # Merge DataFrames on the consistent 'ticker__ticker' column
        try:
            combined_data = pd.merge(
                model_performance_data,
                trade_signal_data,
                on='ticker__ticker',
                how='inner'
            )
            print("Combined Data after first merge:\n", combined_data.head())  # For debugging
        except KeyError as e:
            logger.error(f"Error during merging model_performance_data and trade_signal_data: {e}")
            return pd.DataFrame()

        # Merge with performance_metrics
        if 'ticker__ticker' in performance_metrics.columns:
            try:
                combined_data = pd.merge(
                    combined_data,
                    performance_metrics,
                    on='ticker__ticker',
                    how='inner'
                )
                print("Combined Data after merging performance_metrics:\n", combined_data.head())  # For debugging
            except KeyError as e:
                logger.error(f"Error during merging with performance_metrics: {e}")
                return pd.DataFrame()
        else:
            logger.error("'ticker__ticker' column not found in performance_metrics.")
            return pd.DataFrame()

        # Merge with backtest_data
        if 'ticker__ticker' in backtest_data.columns:
            try:
                cross_referenced_data = pd.merge(
                    combined_data,
                    backtest_data,
                    on='ticker__ticker',
                    how='inner'
                )
                print("Final Cross Referenced Data:\n", cross_referenced_data.head())  # For debugging
            except KeyError as e:
                logger.error(f"Error during merging with backtest_data: {e}")
                return pd.DataFrame()
        else:
            logger.error("'ticker__ticker' column not found in backtest_data.")
            return pd.DataFrame()

        return cross_referenced_data

    # Create chart for predictions vs actual values
    def create_predictions_vs_actuals_chart(self):
        if self.table_exists('model_prediction'):
            predictions = ModelPrediction.objects.all().values(
                'ticker__ticker', 'prediction_value', 'actual_value', 'prediction_date'
            )
            df = pd.DataFrame(predictions)
            print("Model Prediction Data Columns:", df.columns)  # For debugging
            print("Model Prediction Data Sample:\n", df.head())  # For debugging

            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['prediction_date'], y=df['prediction_value'],
                                         mode='lines', name='Predicted Value'))
                fig.add_trace(go.Scatter(x=df['prediction_date'], y=df['actual_value'],
                                         mode='lines', name='Actual Value'))
                fig.update_layout(title="Predictions vs Actual Values",
                                  xaxis_title="Date",
                                  yaxis_title="Price")
                return fig.to_html(full_html=False)
            else:
                logger.info("No data available for ModelPrediction chart.")
                return "<p>No Prediction Data Available.</p>"
        else:
            logger.info("ModelPrediction table does not exist.")
            return "<p>Model Prediction Data Not Available.</p>"

    # Create bar chart for performance metrics (MAE, RMSE, etc.)
    def create_performance_metrics_chart(self, model_performance_data):
        if not model_performance_data.empty:
            try:
                df = model_performance_data
                fig = go.Figure()
                fig.add_trace(go.Bar(x=['MAE'], y=[df['mae'].mean()], name='MAE'))
                fig.add_trace(go.Bar(x=['RMSE'], y=[df['rmse'].mean()], name='RMSE'))
                fig.add_trace(go.Bar(x=['MAPE'], y=[df['mape'].mean()], name='MAPE'))
                fig.add_trace(go.Bar(x=['R2'], y=[df['r2'].mean()], name='R2'))
                fig.update_layout(title="Model Performance Metrics",
                                  xaxis_title="Metrics",
                                  yaxis_title="Value")
                return fig.to_html(full_html=False)
            except KeyError as e:
                logger.error(f"Missing expected column in model_performance_data: {e}")
                return "<p>Performance Metrics Data Incomplete.</p>"
        else:
            logger.info("Model Performance Data is empty. No Performance Metrics chart to display.")
            return "<p>No Performance Metrics Available.</p>"

    # Create a chart to visualize the backtest trade logs
    def create_backtest_trade_logs_chart(self):
        trade_logs = self.get_backtest_trade_logs()
        if not trade_logs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trade_logs['date'], y=trade_logs['portfolio_value'],
                                     mode='lines+markers', name='Portfolio Value'))
            fig.add_trace(go.Scatter(x=trade_logs['date'], y=trade_logs['price'],
                                     mode='markers', name='Trade Prices'))
            fig.update_layout(title="Backtest Trade Logs",
                              xaxis_title="Trade Date",
                              yaxis_title="Portfolio Value / Trade Price")
            return fig.to_html(full_html=False)
        else:
            logger.info("No data available for Backtest Trade Logs chart.")
            return "<p>No Backtest Trade Logs Available.</p>"

    # Fetch trade logs from BackTester.Models (BacktestResultsTradeLogs)
    def get_backtest_trade_logs(self):
        if self.table_exists('backtest_results_trade_logs'):
            trade_logs = BacktestResultsTradeLogs.objects.all().values(
                'ticker__ticker', 'action', 'quantity', 'price', 'date', 'portfolio_value'
            )
            df = pd.DataFrame(trade_logs)
            print("Backtest Trade Logs Data Columns:", df.columns)  # For debugging
            print("Backtest Trade Logs Data Sample:\n", df.head())  # For debugging
            return df
        else:
            logger.info("BacktestResultsTradeLogs table does not exist.")
            return pd.DataFrame()