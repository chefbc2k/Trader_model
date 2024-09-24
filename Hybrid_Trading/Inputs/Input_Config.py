def load_configurations():
    # Load configurations for different modes
    return {
        "full_run": {
            "percentage_options": [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            "interval_options": ["1d"],
            "period_options": ["D"],
            "sentiment_type_options": ["bullish", "bearish", "neutral"],
            "handle_missing_values_options": ["drop", "fill", "interpolate"],
            "fillna_method_options": ["median", "mean", "zero"],
        },
        "backtester": {
            "percentage_options": [1, 5, 10, 15, 25, 50, 60, 75, 100],
            "interval_options": ["1d", "5d", "1w", "1m"],
            "period_options": ["D", "w"],  # Use 'w' for weeks
            "sentiment_type_options": ["bullish", "bearish", "neutral"],
            "handle_missing_values_options": ["drop", "fill", "interpolate"],
            "fillna_method_options": ["mean", "median", "zero"],
        },
        "day_trader": {
            "percentage_options": [1, 10, 15, 25, 50, 60, 70, 80, 90, 100],
            "interval_options": ["1min", "5min", "15min", "30min", "60min"],
            "period_options": ["D", "h"],  # Use 'h' for hours
            "sentiment_type_options": ["bullish", "bearish", "neutral"],
            "handle_missing_values_options": ["interpolate", "fill", "drop"],
            "fillna_method_options": ["mean", "median", "zero"],
        },
        "sentiment_analysis": {
            "sentiment_type_options": ["bullish", "bearish", "neutral"],
            "frequency_options": ["daily", "weekly", "monthly"],
            "tickers_options": [],
            "sentiment_score_threshold_options": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 5.0],  # Example threshold
            "market_cap_filter_options": ["small", "medium", "large", "all"],
            "sector_options": [
                "technology", "healthcare", "finance", "energy", "utilities", "materials",
                "consumer_discretionary", "consumer_staples", "industrials", "real_estate",
                "communication_services"
            ],
            "region_options": ["USA", "Europe", "Asia", "Global"],
            "time_of_day_options": ["morning", "afternoon", "evening"],
            "analyst_consensus_options": ["buy", "hold", "sell"],
            "sentiment_momentum_options": ["increasing", "decreasing", "steady"]
        }
    }