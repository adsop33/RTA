from __future__ import annotations

import random
from typing import Literal
from uuid import uuid4

from producer.catalog import suppliers_by_id
from producer.models import Product, utc_now_iso

Scenario = Literal["normal", "demand_spike"]


class EventGenerator:
    def __init__(self, products: list[Product], scenario: Scenario) -> None:
        self.products = products
        self.scenario = scenario
        self.suppliers = suppliers_by_id()

    def product_events(self) -> list[tuple[str, str, dict]]:
        return [("products", product.product_id, product.to_event()) for product in self.products]

    def supplier_events(self) -> list[tuple[str, str, dict]]:
        return [
            ("suppliers", supplier.supplier_id, supplier.to_event())
            for supplier in self.suppliers.values()
        ]

    def next_sale(self) -> tuple[str, str, dict]:
        product = self._select_product_for_sale()
        quantity = self._sale_quantity()

        event = {
            "event_id": str(uuid4()),
            "event_type": "sale",
            "event_time": utc_now_iso(),
            "scenario": self.scenario,
            "sale_id": f"SALE-{uuid4().hex[:10].upper()}",
            "product_id": product.product_id,
            "product_name": product.name,
            "category": product.category,
            "quantity": quantity,
            "unit_price": product.price,
            "total_amount": round(quantity * product.price, 2),
            "channel": random.choice(["online", "store", "mobile_app"]),
        }
        return "sales", product.product_id, event

    def _select_product_for_sale(self) -> Product:
        if self.scenario == "demand_spike":
            popular_products = sorted(self.products, key=lambda product: product.price, reverse=True)[:3]
            return random.choice(popular_products)

        return random.choice(self.products)

    def _sale_quantity(self) -> int:
        if self.scenario == "demand_spike":
            return random.randint(3, 12)
        return random.randint(1, 4)
