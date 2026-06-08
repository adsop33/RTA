import json
import pandas as pd


class ReportGenerator:

    def __init__(self, config):
        self.config = config


    def load_predictions(self):

        with open(self.config.INPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return pd.DataFrame(data)


    def normalize(self, df: pd.DataFrame):

        df["prediction_D1"] = df["prediction"].apply(lambda x: x["d1"])
        df["prediction_D2"] = df["prediction"].apply(lambda x: x["d2"])
        df["prediction_D3"] = df["prediction"].apply(lambda x: x["d3"])

        df["CI95_LOW"] = df["confidence_interval"].apply(
            lambda x: min(x["d1"][0], x["d2"][0], x["d3"][0])
        )

        df["CI95_HIGH"] = df["confidence_interval"].apply(
            lambda x: max(x["d1"][1], x["d2"][1], x["d3"][1])
        )

        return df


    def build_forecast_report(self, df: pd.DataFrame):

        report = df[[
            "product_id",
            "stock",
            "prediction_D1",
            "prediction_D2",
            "prediction_D3",
            "CI95_LOW",
            "CI95_HIGH",
            "days_to_stockout"
        ]].copy()

        report = report.sort_values("days_to_stockout", ascending=True)

        return report


    def build_risk_report(self, df: pd.DataFrame):

        df["risk"] = df["risk"].astype(bool)

        risk_df = df[df["risk"] == True].copy()

        risk_df = risk_df.sort_values("days_to_stockout", ascending=True)

        return risk_df



    def generate(self):

        df = self.load_predictions()
        df = self.normalize(df)

        forecast = self.build_forecast_report(df)
        risk = self.build_risk_report(df)

        return forecast, risk