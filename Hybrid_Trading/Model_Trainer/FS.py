import logging
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Lasso, Ridge, LogisticRegression, SGDRegressor, PassiveAggressiveRegressor, Perceptron
from sklearn.svm import SVR
from concurrent.futures import ThreadPoolExecutor, as_completed
from alive_progress import alive_bar
from xgboost import XGBRegressor


class FeatureSelector:
    def __init__(self, user_input, method: str = 'k_best', k: int = 10, threshold: float = 0.01):
        self.user_input = user_input
        self.method = method
        self.k = k
        self.threshold = threshold
        logging.info(f"FeatureSelector initialized with method: {method}, k: {k}, threshold: {threshold}")

    def select_features(self, df: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        model_type = self.user_input.args.get('model_type', 'XGBoost')  # Default to XGBoost if not specified
        logging.info(f"Starting feature selection for model type: {model_type}")
        print(f"Selecting features for model type: {model_type}")

        try:
            if self.method == 'k_best':
                return self.k_best_selection(df, target)
            elif self.method == 'mutual_info':
                return self.mutual_info_selection(df, target)
            else:
                return self.model_based_selection(df, target, model_type)
        except Exception as e:
            logging.error(f"Error during feature selection: {e}")
            raise

    def k_best_selection(self, df: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        selector = SelectKBest(score_func=f_regression, k=self.k)
        df_selected = selector.fit_transform(df, target)
        selected_features = df.columns[selector.get_support(indices=True)]
        logging.info(f"Selected top {self.k} features using k_best method: {selected_features}")
        return pd.DataFrame(df_selected, columns=selected_features)

    def mutual_info_selection(self, df: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        selector = SelectKBest(score_func=mutual_info_regression, k=self.k)
        df_selected = selector.fit_transform(df, target)
        selected_features = df.columns[selector.get_support(indices=True)]
        logging.info(f"Selected top {self.k} features using mutual information method: {selected_features}")
        return pd.DataFrame(df_selected, columns=selected_features)

    def model_based_selection(self, df: pd.DataFrame, target: pd.Series, model_type: str) -> pd.DataFrame:
        model = self.get_model(model_type)
        model.fit(df, target)
        importances = model.feature_importances_ if hasattr(model, 'feature_importances_') else model.coef_
        selected_features = df.columns[importances > self.threshold] if hasattr(model, 'feature_importances_') else df.columns[importances != 0]
        df_selected = df[selected_features]
        logging.info(f"Selected features based on {model_type} model importance: {selected_features}")
        return df_selected

    def get_model(self, model_type: str):
        models = {
            'RandomForest': RandomForestRegressor(),
            'GradientBoosting': GradientBoostingRegressor(),
            'Lasso': Lasso(),
            'Ridge': Ridge(),
            'SVM': SVR(),
            'Logistic Regression': LogisticRegression(),
            'SGDRegressor': SGDRegressor(),
            'PassiveAggressiveRegressor': PassiveAggressiveRegressor(),
            'Perceptron': Perceptron(),
            'XGBoost': XGBRegressor()
        }
        return models.get(model_type, XGBRegressor())  # Default to XGBoost

    def run_selection(self, df: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        num_tickers = len(df.columns)
        logging.info(f"Running feature selection on {num_tickers} features.")
        print(f"Running feature selection on {num_tickers} features.")

        selected_features_df = pd.DataFrame()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            with alive_bar(num_tickers, title="Feature Selection Progress") as bar:
                for feature in df.columns:
                    futures.append(executor.submit(self.select_features, df, target))

                for future in as_completed(futures):
                    result = future.result()
                    selected_features_df = pd.concat([selected_features_df, result], axis=1)
                    bar()

        logging.info("Feature selection completed.")
        print("Feature selection completed.")
        return selected_features_df