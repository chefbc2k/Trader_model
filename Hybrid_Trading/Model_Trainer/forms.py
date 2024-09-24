from django import forms

class OrchestrationForm(forms.Form):
    MODEL_CHOICES = [
        ('', 'Choose Model Type'),  # Placeholder option
        ('RandomForest', 'Random Forest'),
        ('XGBoost', 'XGBoost'),
        ('OnlineSGD', 'Online SGD'),
        ('OnlinePassiveAggressive', 'Online Passive Aggressive'),
        ('Perceptron', 'Perceptron'),
        ('SGDRegressor', 'SGD Regressor'),
        ('RNN', 'Recurrent Neural Network'),
        ('AutoARIMA', 'Auto ARIMA')
    ]

    FEATURE_SELECTION_CHOICES = [
        ('', 'Choose Feature Selection Method'),  # Placeholder option
        ('k_best', 'K Best'),
        ('mutual_info', 'Mutual Information'),
        ('model_based', 'Model Based')
    ]

    OPTIMIZATION_CHOICES = [
        ('', 'Choose Optimization Method'),  # Placeholder option
        ('grid_search', 'Grid Search'),
        ('random_search', 'Random Search'),
        ('bayesian_optimization', 'Bayesian Optimization'),
        ('auto_arima', 'Auto ARIMA'),
        ('time_series_cv', 'Time Series Cross-Validation')
    ]

    SCORING_CHOICES = [
        ('', 'Choose Scoring Method'),  # Placeholder option
        ('neg_mean_squared_error', 'Negative Mean Squared Error'),
        ('r2', 'R-squared'),
        ('neg_mean_absolute_percentage_error', 'MAPE'),
    ]

    AUTO_ARIMA_CHOICES = [
        ('', 'Choose Auto ARIMA Parameters'),  # Placeholder option
        ('auto_arima_1', 'Auto ARIMA 1'),
        ('auto_arima_2', 'Auto ARIMA 2'),
        ('auto_arima_3', 'Auto ARIMA 3'),
        ('auto_arima_4', 'Auto ARIMA 4'),
        ('auto_arima_5', 'Auto ARIMA 5')
    ]

    TIME_SERIES_CV_CHOICES = [
        ('', 'Choose Time Series CV Parameters'),  # Placeholder option
        ('time_series_cv_1', 'Time Series CV 1'),
        ('time_series_cv_2', 'Time Series CV 2'),
        ('time_series_cv_3', 'Time Series CV 3'),
        ('time_series_cv_4', 'Time Series CV 4'),
        ('time_series_cv_5', 'Time Series CV 5')
    ]

    RETURN_FORMAT_CHOICES = [
        ('', 'Choose Return Format'),  # Placeholder option
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('html', 'HTML'),
        ('pdf', 'PDF')
    ]

    # Ticker percentage choices
    PERCENTAGE_CHOICES = [
        (1, '1%'),
        (5, '5%'),
        (10, '10%'),
        (20, '20%'),
        (30, '30%'),
        (40, '40%'),
        (50, '50%'),
        (60, '60%'),
        (70, '70%'),
        (80, '80%'),
        (90, '90%'),
        (100, '100%')
    ]

    # Form fields
    model_type = forms.ChoiceField(choices=MODEL_CHOICES, label="Model Type", required=True)
    feature_selection_method = forms.ChoiceField(choices=FEATURE_SELECTION_CHOICES, label="Feature Selection Method", required=True)
    number_of_features = forms.IntegerField(min_value=1, label="Number of Features to Select", required=True)
    optimization_method = forms.ChoiceField(choices=OPTIMIZATION_CHOICES, label="Optimization Method", required=True)
    scoring = forms.ChoiceField(choices=SCORING_CHOICES, label="Scoring Method", required=True)
    
    # Dropdowns for Auto ARIMA and Time Series CV parameters
    auto_arima_params = forms.ChoiceField(choices=AUTO_ARIMA_CHOICES, label="Auto ARIMA Parameters", required=False)
    time_series_cv_params = forms.ChoiceField(choices=TIME_SERIES_CV_CHOICES, label="Time Series CV Parameters", required=False)
    
    # Performance Thresholds
    mape_threshold = forms.FloatField(label="MAPE Threshold", required=False, initial=0.1)
    rmse_threshold = forms.FloatField(label="RMSE Threshold", required=False)
    mae_threshold = forms.FloatField(label="MAE Threshold", required=False)
    r2_threshold = forms.FloatField(label="R2 Threshold", required=False)

    # Target Column Options
    target_column = forms.ChoiceField(choices=[
        ('', 'Choose Target Column'),  # Placeholder option
        ('open', 'Open Price'),
        ('close', 'Close Price'),
        ('volume', 'Volume'),
        ('price_target', 'Price Target'),
        ('price', 'Price')
    ], label="Target Column", initial="")

    # Date Range
    start_date = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date", required=True)
    end_date = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), label="End Date", required=True)

    # Batch Size and Train/Test Split
    batch_size = forms.IntegerField(min_value=1, label="Batch Size", required=True)
    train_test_split_ratio = forms.FloatField(min_value=0.1, max_value=0.9, label="Train/Test Split Ratio", initial=0.8)

    # Additional Custom Settings
    scaling_preference = forms.ChoiceField(
        choices=[('', 'Choose Scaling/Normalization Preference'), ('scaling', 'Scaling'), ('normalization', 'Normalization')],
        label="Scaling/Normalization Preference",
        required=False
    )

    # Ticker percentage to process
    percentage = forms.ChoiceField(choices=PERCENTAGE_CHOICES, label="Percentage of Tickers to Process", required=True)
    
    # Concurrency Configuration
    concurrency = forms.IntegerField(min_value=1, label="Concurrency (Optional)", required=False)
    
    # New field for return format
    return_format = forms.ChoiceField(choices=RETURN_FORMAT_CHOICES, label="Return Format", required=True)

    def clean(self):
        cleaned_data = super().clean()

        model_type = cleaned_data.get("model_type")
        feature_selection_method = cleaned_data.get("feature_selection_method")
        optimization_method = cleaned_data.get("optimization_method")

        # Suggestions based on selections
        suggestions = {}

        # Suggest correct feature selection if invalid
        if model_type in ['RandomForest', 'XGBoost', 'RNN'] and feature_selection_method not in ['k_best', 'mutual_info']:
            suggestions['feature_selection_method'] = "For the selected model, the recommended feature selection methods are 'K Best' or 'Mutual Information'."

        # Suggest correct optimization method if invalid
        if optimization_method == 'auto_arima' and model_type != 'AutoARIMA':
            suggestions['optimization_method'] = "Auto ARIMA optimization can only be used with the Auto ARIMA model."

        if feature_selection_method == 'model_based' and model_type in ['Perceptron', 'OnlineSGD', 'SGDRegressor']:
            suggestions['feature_selection_method'] = "Model-based feature selection cannot be used with Perceptron, SGD models."

        # Chain validations for Auto ARIMA and Time Series CV
        if model_type == 'AutoARIMA' and not cleaned_data.get("auto_arima_params"):
            suggestions['auto_arima_params'] = "Please select valid Auto ARIMA parameters for the Auto ARIMA model."

        if feature_selection_method == 'time_series_cv' and not cleaned_data.get("time_series_cv_params"):
            suggestions['time_series_cv_params'] = "Please select valid Time Series CV parameters when using Time Series CV."

        # Ensure that all threshold metrics are logical and within valid ranges
        mape_threshold = cleaned_data.get('mape_threshold')
        rmse_threshold = cleaned_data.get('rmse_threshold')
        mae_threshold = cleaned_data.get('mae_threshold')

        if mape_threshold and (mape_threshold < 0 or mape_threshold > 1):
            suggestions['mape_threshold'] = "MAPE threshold should be between 0 and 1."

        if rmse_threshold and rmse_threshold < 0:
            suggestions['rmse_threshold'] = "RMSE threshold cannot be negative."

        # Return suggestions to guide the user instead of raising errors
        if suggestions:
            return suggestions
        return cleaned_data