import joblib
import numpy as np
import pandas as pd


class PredictionEngine:

    def __init__(self, config):

        self.config = config

        best_model_name = open(
            f"{config.MODEL_DIR}/best_model.txt"
        ).read().strip()

        self.model = joblib.load(
            f"{config.MODEL_DIR}/{best_model_name}_sales.pkl"
        )

    def predict(self, features: dict):

        df = pd.DataFrame([features])

        pred = self.model.predict(df)[0]

        return {
            "d1": max(0, float(pred[0])),
            "d2": max(0, float(pred[1])),
            "d3": max(0, float(pred[2]))
        }