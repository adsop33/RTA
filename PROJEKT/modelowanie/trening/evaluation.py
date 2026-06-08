import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


class Evaluator:


    @staticmethod
    def _mape(y_true, y_pred):
        """
        Mean Absolute Percentage Error
        Safe version (avoids division by zero)
        """
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)

        epsilon = 1e-8

        return np.mean(
            np.abs((y_true - y_pred) / (y_true + epsilon))
        )

    @staticmethod
    def _rmse(y_true, y_pred):
        return np.sqrt(mean_squared_error(y_true, y_pred))

    @staticmethod
    def _mae(y_true, y_pred):
        return mean_absolute_error(y_true, y_pred)


    @staticmethod
    def evaluate_single_horizon(y_true, y_pred):
        return {
            "MAE": float(Evaluator._mae(y_true, y_pred)),
            "RMSE": float(Evaluator._rmse(y_true, y_pred)),
            "MAPE": float(Evaluator._mape(y_true, y_pred)),
        }


    @staticmethod
    def evaluate_multi_horizon(y_true: pd.DataFrame, y_pred: np.ndarray):
        """
        y_true: DataFrame with columns:
            target_d1, target_d2, target_d3

        y_pred: np.array shape (n_samples, 3)
        """

        results = {}

        horizons = ["d1", "d2", "d3"]

        all_mapes = []

        for i, h in enumerate(horizons):

            true_vals = y_true[f"target_{h}"].values
            pred_vals = y_pred[:, i]

            metrics = Evaluator.evaluate_single_horizon(
                true_vals,
                pred_vals
            )

            results[h] = metrics

            all_mapes.append(metrics["MAPE"])

        results["global"] = {
            "MAE": float(np.mean([
                results[h]["MAE"] for h in horizons
            ])),
            "RMSE": float(np.mean([
                results[h]["RMSE"] for h in horizons
            ])),
            "MAPE": float(np.mean(all_mapes))
        }

        return results


    @staticmethod
    def compute_residuals(y_true: pd.DataFrame, y_pred: np.ndarray):
        """
        Returns residual distributions per horizon:
        used later for CI estimation in predictor module
        """

        residuals = {
            "d1": (y_true["target_d1"].values - y_pred[:, 0]),
            "d2": (y_true["target_d2"].values - y_pred[:, 1]),
            "d3": (y_true["target_d3"].values - y_pred[:, 2]),
        }

        return residuals


    @staticmethod
    def compare_models(eval_linear: dict, eval_mlp: dict):
        """
        Chooses best model based on global MAPE
        """

        if eval_linear["global"]["MAPE"] < eval_mlp["global"]["MAPE"]:
            return "linear"
        return "mlp"