import json
import pandas as pd


class DataLoader:

    @staticmethod
    def load_products(path: str) -> pd.DataFrame:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return pd.DataFrame(data)

    @staticmethod
    def load_sales(path: str) -> pd.DataFrame:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        df["event_time"] = pd.to_datetime(df["event_time"])

        df = df[df["event_type"] == "sale"]

        df = df.sort_values("event_time").reset_index(drop=True)

        return df

    @staticmethod
    def load_deliveries(path: str) -> pd.DataFrame:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data)


        return df