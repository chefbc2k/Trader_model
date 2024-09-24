import logging
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from skopt import BayesSearchCV
from skopt.space import Real, Categorical, Integer
import pandas as pd
from pmdarima import auto_arima  # For Auto ARIMA
from typing import Dict, Any


class HyperOptimization:
    def __init__(self, user_input: Dict[str, Any], model):
        self.user_input = user_input
        self.model = model
        self.optimization_method = self.user_input.get('optimization_method', 'grid_search')
        self.search_space = self.define_search_space()  # Dynamically define the search space using skopt
        self.n_iter = self.user_input.get('n_iter', 50)
        self.cv_folds = self.user_input.get('cv_folds', 5)
        self.scoring = self.user_input.get('scoring', 'neg_mean_squared_error')
        self.settings = user_input.get('training_settings', {})  # Load training settings if available
        self.auto_arima_params = self.user_input.get('auto_arima_params', {})  # For Auto ARIMA
        self.time_series_cv_params = self.user_input.get('time_series_cv_params', {})  # For Time Series CV

        logging.info(f"HyperOptimization initialized with method: {self.optimization_method}")

    def define_search_space(self):
        """Define the search space dynamically using Real, Integer, and Categorical."""
        # Example: Update this function based on your model's parameter tuning needs
        return {
            'param_1': Real(0.01, 1.0, prior='log-uniform'),
            'param_2': Integer(1, 100),
            'param_3': Categorical(['option_1', 'option_2', 'option_3'])
        }

    def bayesian_optimization(self, X, y):
        logging.info("Starting Bayesian Optimization...")
        bayes_search = BayesSearchCV(
            estimator=self.model,
            search_spaces=self.search_space,
            n_iter=self.n_iter,
            cv=self.cv_folds,
            scoring=self.scoring,
            n_jobs=-1,
            verbose=1,
            random_state=self.settings.get('random_seed', 42)
        )
        bayes_search.fit(X, y)
        logging.info("Bayesian Optimization complete.")
        best_params_df = pd.DataFrame([bayes_search.best_params_], index=['Best Params'])
        logging.info(f"Best Bayesian Parameters: \n{best_params_df}")
        return bayes_search.best_estimator_, bayes_search.best_params_

    def random_search_optimization(self, X, y):
        logging.info("Starting Random Search Optimization...")
        random_search = RandomizedSearchCV(
            estimator=self.model,
            param_distributions=self.search_space,
            n_iter=self.n_iter,
            cv=self.cv_folds,
            scoring=self.scoring,
            n_jobs=-1,
            verbose=1,
            random_state=self.settings.get('random_seed', 42)
        )
        random_search.fit(X, y)
        logging.info("Random Search Optimization complete.")
        best_params_df = pd.DataFrame([random_search.best_params_], index=['Best Params'])
        logging.info(f"Best Random Search Parameters: \n{best_params_df}")
        return random_search.best_estimator_, random_search.best_params_

    def grid_search_optimization(self, X, y):
        logging.info("Starting Grid Search Optimization...")
        grid_search = GridSearchCV(
            estimator=self.model,
            param_grid=self.search_space,
            cv=self.cv_folds,
            scoring=self.scoring,
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X, y)
        logging.info("Grid Search Optimization complete.")
        best_params_df = pd.DataFrame([grid_search.best_params_], index=['Best Params'])
        logging.info(f"Best Grid Search Parameters: \n{best_params_df}")
        return grid_search.best_estimator_, grid_search.best_params_

    def time_series_cross_validation_optimization(self, X, y):
        logging.info("Starting Time Series Cross-Validation Optimization...")
        n_splits = self.time_series_cv_params.get('n_splits', 5)
        max_train_size = self.time_series_cv_params.get('max_train_size', None)
        
        tscv = TimeSeriesSplit(n_splits=n_splits, max_train_size=max_train_size)
        
        grid_search = GridSearchCV(
            estimator=self.model,
            param_grid=self.search_space,
            cv=tscv,
            scoring=self.scoring,
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X, y)
        logging.info("Time Series Cross-Validation Optimization complete.")
        best_params_df = pd.DataFrame([grid_search.best_params_], index=['Best Params'])
        logging.info(f"Best Time Series CV Parameters: \n{best_params_df}")
        return grid_search.best_estimator_, grid_search.best_params_

    def auto_arima_optimization(self, X, y):
        logging.info("Starting Auto ARIMA Optimization...")
        arima_model = auto_arima(
            y,
            start_p=self.auto_arima_params.get('start_p', 1),
            start_q=self.auto_arima_params.get('start_q', 1),
            max_p=self.auto_arima_params.get('max_p', 5),
            max_q=self.auto_arima_params.get('max_q', 5),
            d=self.auto_arima_params.get('d', None),
            seasonal=self.auto_arima_params.get('seasonal', False),
            stepwise=self.auto_arima_params.get('stepwise', True),
            suppress_warnings=True,
            random_state=self.settings.get('random_seed', 42),
            n_jobs=-1
        )
        logging.info("Auto ARIMA Optimization complete.")
        return arima_model

    def run_hyper_op(self, X, y):
        logging.info(f"Running optimization method: {self.optimization_method}")
        
        if self.optimization_method == 'bayesian':
            return self.bayesian_optimization(X, y)
        elif self.optimization_method == 'random_search':
            return self.random_search_optimization(X, y)
        elif self.optimization_method == 'grid_search':
            return self.grid_search_optimization(X, y)
        elif self.optimization_method == 'time_series_cv':
            return self.time_series_cross_validation_optimization(X, y)
        elif self.optimization_method == 'auto_arima':
            return self.auto_arima_optimization(X, y)
        else:
            raise ValueError(f"Unknown optimization method: {self.optimization_method}")