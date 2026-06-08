import joblib
import numpy as np


class ConfidenceInterval:

    def __init__(self, config):

        residuals = joblib.load(
            f"{config.MODEL_DIR}/residuals.pkl"
        )

        self.std = {
            "d1": np.std(residuals["d1"]),
            "d2": np.std(residuals["d2"]),
            "d3": np.std(residuals["d3"]),
        }

        self.z = config.CI_Z_SCORE

    def compute(self, prediction: dict):

        return {
            "d1": (
                prediction["d1"] - self.z * self.std["d1"],
                prediction["d1"] + self.z * self.std["d1"]
            ),
            "d2": (
                prediction["d2"] - self.z * self.std["d2"],
                prediction["d2"] + self.z * self.std["d2"]
            ),
            "d3": (
                prediction["d3"] - self.z * self.std["d3"],
                prediction["d3"] + self.z * self.std["d3"]
            )
        }