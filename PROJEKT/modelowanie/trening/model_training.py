import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.multioutput import MultiOutputRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor


class ModelTrainer:

    def __init__(self, config):

        self.config = config

        self.feature_columns = [
            "sales_1d",
            "sales_3d",
            "sales_7d",
            "sales_14d",
            "sales_30d",
            "avg_sales_7d",
            "avg_sales_30d",
            "std_sales_7d",
            "std_sales_30d",
            "trend_7d",
            "price",
            "reorder_level",
            "current_stock",
            "category"
        ]

        self.target_columns = [
            "target_d1",
            "target_d2",
            "target_d3"
        ]


    def build_preprocessor(self):

        numeric_features = [
            f for f in self.feature_columns
            if f != "category"
        ]

        categorical_features = ["category"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
            ]
        )

        return preprocessor


    def build_linear_model(self):

        return Pipeline([
            ("prep", self.build_preprocessor()),
            ("model", MultiOutputRegressor(LinearRegression()))
        ])

    def build_mlp_model(self):

        mlp = MLPRegressor(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            max_iter=1000,
            random_state=self.config.RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1
        )

        return Pipeline([
            ("prep", self.build_preprocessor()),
            ("model", MultiOutputRegressor(mlp))
        ])


    def train(self, X_train, y_train, X_test, y_test, evaluator):

        linear_model = self.build_linear_model()
        mlp_model = self.build_mlp_model()

        print("Training Linear Regression model...")
        linear_model.fit(X_train, y_train)

        print("Training MLP model...")
        mlp_model.fit(X_train, y_train)

        linear_pred = linear_model.predict(X_test)
        mlp_pred = mlp_model.predict(X_test)

        linear_eval = evaluator.evaluate_multi_horizon(
            y_test,
            linear_pred
        )

        mlp_eval = evaluator.evaluate_multi_horizon(
            y_test,
            mlp_pred
        )

        best_model_name = evaluator.compare_models(
            linear_eval,
            mlp_eval
        )

        if best_model_name == "linear":
            best_model = linear_model
            best_pred = linear_pred
            best_eval = linear_eval
        else:
            best_model = mlp_model
            best_pred = mlp_pred
            best_eval = mlp_eval

        residuals = evaluator.compute_residuals(
            y_test,
            best_pred
        )

        return {
            "linear_model": linear_model,
            "mlp_model": mlp_model,
            "best_model": best_model,
            "best_model_name": best_model_name,
            "linear_eval": linear_eval,
            "mlp_eval": mlp_eval,
            "best_eval": best_eval,
            "residuals": residuals
        }