import pandas as pd
import numpy as np


class FeatureEngineer:

    def __init__(self, config):
        self.config = config

    def build_features(self, history_df, product_id, stock, product_meta):

        df = history_df.copy()

        df = df[df["product_id"] == product_id]

        if df.empty:
            return {
                "sales_1d": 0,
                "sales_3d": 0,
                "sales_7d": 0,
                "sales_14d": 0,
                "sales_30d": 0,
                "avg_sales_7d": 0,
                "avg_sales_30d": 0,
                "std_sales_7d": 0,
                "std_sales_30d": 0,
                "trend_7d": 0,
                "price": product_meta["price"],
                "reorder_level": product_meta["reorder_level"],
                "current_stock": stock,
                "category": product_meta["category"]
            }

        df = df.sort_values("event_time")

        q = df["quantity"]

        return {
            "sales_1d": q.tail(1).sum(),
            "sales_3d": q.tail(3).sum(),
            "sales_7d": q.tail(7).sum(),
            "sales_14d": q.tail(14).sum(),
            "sales_30d": q.tail(30).sum(),
            "avg_sales_7d": q.tail(7).mean(),
            "avg_sales_30d": q.tail(30).mean(),
            "std_sales_7d": q.tail(7).std(),
            "std_sales_30d": q.tail(30).std(),
            "trend_7d": q.tail(7).mean() - q.tail(30).mean(),
            "price": product_meta["price"],
            "reorder_level": product_meta["reorder_level"],
            "current_stock": stock,
            "category": product_meta["category"]
        }