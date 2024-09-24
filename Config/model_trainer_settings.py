import os

# General model settings
MODEL_SETTINGS = {
    "forecast_length": [30, 60, 90],  # Options for forecast length
    "frequency": ["D", "W", "M"],  # Frequency options: Daily, Weekly, Monthly
    "ensemble": ["simple", "stacked"],  # Ensemble methods available
    "model_list": ["superfast", "default", "all"],  # Model list options
    "metric_weighting": {
        "smape_weight": 0.5,
        "mae_weight": 0.5,
        "rmse_weight": 0.0
    },
    "validation_method": ["backwards", "rolling"],  # Validation methods
    "max_epochs": 100,  # Maximum number of training epochs
    "early_stopping": True,  # Whether to use early stopping
    "early_stopping_patience": 10,  # Patience for early stopping
    "random_seed": 42,  # Seed for reproducibility
    "model_save_path": "/path/to/save/models/",  # Path to save trained models
    "model_load_path": "/path/to/load/models/",  # Path to load models for evaluation
    "default_model_name": "trained_model.pkl",  # Default model file name
}

# Data preprocessing options
PREPROCESSING_OPTIONS = {
    "normalize": [True, False],  # Options to normalize data
    "scaling_method": ["minmax", "standard"],  # Scaling methods available
    "handle_missing_values": ["interpolate", "drop", "fill"],  # Options for handling missing values
    "fillna_method": ["mean", "median", "zero"],  # Methods to fill NaNs
}

# Visualization settings
VISUALIZATION_SETTINGS = {
    "line_colors": {
        "actual": "blue",  # Color for actual data line
        "forecast": "orange",  # Color for forecasted data line
        "confidence_interval": "lightgray"  # Color for confidence interval shading
    },
    "output_format": ["html", "png", "svg"],  # Output formats available
    "show_confidence_interval": [True, False],  # Options to display confidence intervals
    "title_font_size": 14,  # Font size for plot titles
    "axis_label_font_size": 12,  # Font size for axis labels
}

# Logging settings
LOGGING_SETTINGS = {
    "level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],  # Logging levels available
    "log_to_file": True,  # Whether to log to a file
    "log_file_path": os.path.join(MODEL_SETTINGS["model_save_path"], "forecasting.log"),  # Path for the log file
    "format": "%(asctime)s - %(levelname)s - %(message)s",  # Log format
}

# Default models
DEFAULT_MODELS = {
    "short_term": ["AutoTS", "ETS", "ARIMA", "Prophet", "SARIMA"],  # Default model options for short-term forecasts
    "long_term": ["AutoTS", "ETS", "ARIMA", "Prophet", "SARIMA"],  # Default model options for long-term forecasts
}

# Forecasting horizons
FORECAST_HORIZONS = {
    "short_term": [30, 60, 90],  # Options for short-term forecast steps
    "long_term": [90, 180, 365],  # Options for long-term forecast steps
}

# Training settings
TRAINING_SETTINGS = {
    "train_test_split_ratio": [0.7, 0.8, 0.9],  # Train-test split ratios
    "cross_validation_folds": [3, 5, 10],  # Number of cross-validation folds
    "batch_size": [16, 32, 64],  # Batch sizes for training
    "learning_rate": [0.001, 0.01, 0.1],  # Learning rates for training
    "optimizer": ["adam", "sgd"],  # Optimizers available
}

# Optimization settings
OPTIMIZATION_SETTINGS = {
    "optimize_hyperparameters": [True, False],  # Whether to perform hyperparameter optimization
    "evaluation_metric": ["RMSE", "MAE", "MAPE"],  # Metrics to optimize
    "optimization_trials": [50, 100, 200],  # Number of optimization trials
    "timeout": [1800, 3600, 7200],  # Maximum time for optimization (seconds)
}

# Fallback models
FALLBACK_MODELS = {
    "short_term": "ExponentialSmoothing",  # Fallback model for short-term
    "long_term": "ETS",  # Fallback model for long-term
}

# TensorFlow settings
TENSORFLOW_SETTINGS = {
    "use_gpu": True,  # Whether to use GPU for training
    "gpu_memory_growth": True,  # Allow GPU memory growth
    "autotune_buffer_size": True,  # Use AUTOTUNE for buffer sizes
    "tf_function_retrace": {
        "reduce_retracing": True,  # Reduce retracing for functions
        "trace_limit": 4  # Maximum number of traces allowed
    },
    "use_mixed_precision": False,  # Whether to use mixed precision
    "eager_execution": False,  # Enable or disable eager execution
}