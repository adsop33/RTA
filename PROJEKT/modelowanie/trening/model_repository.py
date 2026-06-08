import os
import json
import joblib
from datetime import datetime


class ModelRepository:

    def __init__(self, config):
        self.config = config


    def save(self, results, feature_columns):

        os.makedirs(self.config.MODEL_DIR, exist_ok=True)


        joblib.dump(
            results["linear_model"],
            os.path.join(self.config.MODEL_DIR, "linear_sales.pkl")
        )

        joblib.dump(
            results["mlp_model"],
            os.path.join(self.config.MODEL_DIR, "mlp_sales.pkl")
        )

        joblib.dump(
            results["best_model"],
            os.path.join(self.config.MODEL_DIR, "best_model.pkl")
        )


        joblib.dump(
            results["residuals"],
            os.path.join(self.config.MODEL_DIR, "residuals.pkl")
        )


        with open(os.path.join(self.config.MODEL_DIR, "best_model.txt"), "w") as f:
            f.write(results["best_model_name"])


        metadata = {
            "best_model": results["best_model_name"],
            "training_date": datetime.utcnow().isoformat(),
            "feature_version": "1.0",
            "feature_columns": feature_columns
        }

        with open(os.path.join(self.config.MODEL_DIR, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)


        evaluation = {
            "linear": results["linear_eval"],
            "mlp": results["mlp_eval"],
            "best": results["best_eval"]
        }

        with open(os.path.join(self.config.MODEL_DIR, "evaluation.json"), "w") as f:
            json.dump(evaluation, f, indent=4)