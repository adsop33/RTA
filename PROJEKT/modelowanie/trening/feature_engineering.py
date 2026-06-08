import pandas as pd
import numpy as np


class FeatureEngineer:

    def __init__(self, config):
        self.config = config


    def compute_stock_history(self, products_df, sales_df, deliveries_df):

        products = products_df.copy()

        stock_map = {
            row["product_id"]: row["initial_stock"]
            for _, row in products.iterrows()
        }

        sales_df = sales_df.copy()
        deliveries_df = deliveries_df.copy()

        sales_df["delta"] = -sales_df["quantity"]
        deliveries_df["delta"] = deliveries_df["quantity"]

        sales_df = sales_df[[
            "event_time", "product_id", "delta"
        ]]

        deliveries_df = deliveries_df[[
            "product_id", "delta"
        ]]

        stock_history = []

        for product_id in stock_map.keys():

            prod_sales = sales_df[sales_df["product_id"] == product_id]
            prod_deliv = deliveries_df[deliveries_df["product_id"] == product_id]

            total_sales = prod_sales["delta"].sum()
            total_deliv = prod_deliv["delta"].sum()

            current_stock = stock_map[product_id] + total_deliv + total_sales

            stock_history.append({
                "product_id": product_id,
                "current_stock": current_stock
            })

        return pd.DataFrame(stock_history)


    def build_daily_sales(self, sales_df: pd.DataFrame):

        daily = (
            sales_df
            .groupby([
                "product_id",
                pd.Grouper(key="event_time", freq=self.config.DAILY_FREQ)
            ])["quantity"]
            .sum()
            .reset_index()
            .rename(columns={"event_time": "date"})
        )

        return daily


    def build_dataset(self, products_df, sales_df, deliveries_df):

        daily_sales = self.build_daily_sales(sales_df)

        stock_df = self.compute_stock_history(
            products_df,
            sales_df,
            deliveries_df
        )

        products_df = products_df.copy()

        dataset = []

        for product_id in products_df["product_id"].unique():

            product_meta = products_df[
                products_df["product_id"] == product_id
            ].iloc[0]

            df = daily_sales[
                daily_sales["product_id"] == product_id
            ].copy()

            if df.empty:
                continue

            df = df.sort_values("date")


            df["sales_1d"] = df["quantity"]

            for w in self.config.ROLLING_WINDOWS:

                df[f"sales_{w}d"] = (
                    df["quantity"].rolling(w).sum()
                )

                df[f"avg_sales_{w}d"] = (
                    df["quantity"].rolling(w).mean()
                )

                df[f"std_sales_{w}d"] = (
                    df["quantity"].rolling(w).std()
                )

            df["trend_7d"] = (
                df["avg_sales_7d"] - df["avg_sales_30d"]
            )


            df["days_since_last_sale"] = (
                df["quantity"].gt(0).cumsum()
            )


            current_stock = stock_df[
                stock_df["product_id"] == product_id
            ]["current_stock"].values[0]

            df["current_stock"] = current_stock


            df["category"] = product_meta["category"]
            df["price"] = product_meta["price"]
            df["reorder_level"] = product_meta["reorder_level"]


            df["target_d1"] = df["quantity"].shift(-1)
            df["target_d2"] = df["quantity"].shift(-2)
            df["target_d3"] = df["quantity"].shift(-3)

            dataset.append(df)

        final_df = pd.concat(dataset, ignore_index=True)

        final_df = final_df.dropna()

        return final_df