import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool, Span, BoxAnnotation, Label, Panel, Tabs, LinearAxis, Range1d
import logging
from Config.model_trainer_settings import VISUALIZATION_SETTINGS

class MTVisualization:
    def __init__(self, user_visualization_settings=None):
        # Allow overriding default visualization settings
        if user_visualization_settings:
            self.visualization_settings = user_visualization_settings
        else:
            self.visualization_settings = VISUALIZATION_SETTINGS

    def visualize_forecast(
        self,
        actual,
        forecast,
        model_name,
        ticker,
        decision,
        signals=None,
        performance_metrics=None,
        trend_lines=None,
        sentiment_overlay=None,
        volume=None,
        key_events=None,
        highlight_ranges=None  # Highlight regions using BoxAnnotation
    ):
        # Create DataFrames for actual and forecasted values
        actual_df = pd.DataFrame(actual)
        forecast_df = pd.DataFrame(forecast)

        # Check DataFrame structure for debugging
        logging.debug(f"Actual DataFrame shape: {actual_df.shape}")
        logging.debug(f"Forecast DataFrame shape: {forecast_df.shape}")

        # Check if the DataFrames are empty
        if actual_df.empty:
            logging.error("Actual data DataFrame is empty. Cannot visualize forecast.")
            return
        if forecast_df.empty:
            logging.error("Forecast data DataFrame is empty. Cannot visualize forecast.")
            return

        # Ensure the indices are date types for plotting
        if not pd.api.types.is_datetime64_any_dtype(actual_df.index):
            actual_df.index = pd.to_datetime(actual_df.index)
        if not pd.api.types.is_datetime64_any_dtype(forecast_df.index):
            forecast_df.index = pd.to_datetime(forecast_df.index)

        # Set up Bokeh figure
        p = figure(
            x_axis_type="datetime",
            title=f"Forecast using {model_name} for {ticker} - Decision: {decision}",
            height=400,
            width=800,
            tools="pan,box_zoom,reset,save",
        )

        # Add HoverTool with formatted tooltips
        hover = HoverTool(
            tooltips=[
                ("Date", "@x{%F}"),
                ("Value", "@y{0.2f}")
            ],
            formatters={
                '@x': 'datetime'
            },
            mode='vline'
        )
        p.add_tools(hover)

        # Plot actual and forecasted data
        p.line(actual_df.index, actual_df.iloc[:, 0], legend_label="Actual", line_color=self.visualization_settings['line_colors']['actual'])
        p.line(forecast_df.index, forecast_df.iloc[:, 0], legend_label="Forecast", line_color=self.visualization_settings['line_colors']['forecast'])

        # Add confidence intervals
        if self.visualization_settings['show_confidence_interval'][0]:
            lower_bound = forecast_df.iloc[:, 0] - 1.96 * forecast_df.iloc[:, 1]
            upper_bound = forecast_df.iloc[:, 0] + 1.96 * forecast_df.iloc[:, 1]
            p.varea(x=forecast_df.index, y1=lower_bound, y2=upper_bound, color=self.visualization_settings['line_colors']['confidence_interval'], alpha=0.2, legend_label="Confidence Interval")

        # Plot trading signals
        if signals is not None:
            for idx, signal in signals.iterrows():
                if signal['signal'] == 'BUY':
                    p.triangle(signal['date'], signal['price'], size=10, color="green", legend_label="Buy Signal")
                elif signal['signal'] == 'SELL':
                    p.inverted_triangle(signal['date'], signal['price'], size=10, color="red", legend_label="Sell Signal")

        # Add trend lines
        if trend_lines is not None:
            for trend in trend_lines:
                p.line(trend['x'], trend['y'], line_dash="dashed", line_width=2, color="orange", legend_label="Trend Line")

        # Overlay sentiment analysis
        if sentiment_overlay is not None:
            sentiment_df = pd.DataFrame(sentiment_overlay)
            if not sentiment_df.empty:
                p.extra_y_ranges = {"sentiment": Range1d(start=0, end=100)}
                p.add_layout(LinearAxis(y_range_name="sentiment"), 'right')
                p.line(sentiment_df.index, sentiment_df['sentiment'], color="purple", y_range_name="sentiment", legend_label="Sentiment")

        # Plot volume
        if volume is not None:
            volume_df = pd.DataFrame(volume)
            if not volume_df.empty:
                p.vbar(x=volume_df.index, top=volume_df['volume'], width=0.5, alpha=0.3, color="gray", legend_label="Volume")

        # Annotate key events or news
        if key_events is not None:
            for event in key_events:
                span = Span(location=event['date'], dimension='height', line_color='red', line_dash='dashed', line_width=1)
                p.add_layout(span)
                label = Label(x=event['date'], y=max(forecast_df.iloc[:, 0]), text=event['description'], render_mode='css')
                p.add_layout(label)

        # Display performance metrics as annotations
        if performance_metrics is not None:
            metrics_text = "\n".join([f"{k}: {v:.2f}" for k, v in performance_metrics.items()])
            label = Label(x=0, y=1, x_units='screen', y_units='screen', text=metrics_text, render_mode='css', border_line_color='black', border_line_alpha=1.0, background_fill_color='white', background_fill_alpha=1.0)
            p.add_layout(label)

        # Highlight specific ranges using BoxAnnotation
        if highlight_ranges is not None:
            for highlight in highlight_ranges:
                box = BoxAnnotation(
                    left=highlight.get('left', None),  # start of the box (date or value)
                    right=highlight.get('right', None),  # end of the box (date or value)
                    top=highlight.get('top', None),  # upper bound (price or value)
                    bottom=highlight.get('bottom', None),  # lower bound (price or value)
                    fill_color=highlight.get('color', 'lightgrey'),
                    fill_alpha=highlight.get('alpha', 0.3)
                )
                p.add_layout(box)

        # Tabs for different analysis types (if needed)
        tabs = [Panel(child=p, title="Main Plot")]

        # Output the plot to a file and display it
        output_file(f"{model_name}_{ticker}_forecast.html")
        show(Tabs(tabs=tabs))