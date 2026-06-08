from collections import defaultdict


class InventoryManager:

    def __init__(self, products_df):

        self.stock = {
            row["product_id"]: row["initial_stock"]
            for _, row in products_df.iterrows()
        }

    def apply_sale(self, product_id: str, quantity: int):
        self.stock[product_id] -= quantity

    def apply_delivery(self, product_id: str, quantity: int):
        self.stock[product_id] += quantity

    def get_stock(self, product_id: str):
        return self.stock.get(product_id, 0)