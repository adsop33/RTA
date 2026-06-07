from __future__ import annotations

import json
from pathlib import Path

from producer.models import Product, Supplier


SUPPLIERS: tuple[Supplier, ...] = (
    Supplier("S001", "TechDistribution Polska", "PL", 3),
    Supplier("S002", "EuroMonitors GmbH", "DE", 4),
    Supplier("S003", "Nordic Accessories", "SE", 5),
    Supplier("S004", "Storage World", "CZ", 2),
    Supplier("S005", "Network Partner", "PL", 3),
    Supplier("S006", "Mobile Europe", "NL", 6),
    Supplier("S007", "Audio Premium", "JP", 8),
)


def load_products(path: Path) -> list[Product]:
    with path.open("r", encoding="utf-8") as source:
        rows = json.load(source)

    return [Product(**row) for row in rows]


def suppliers_by_id() -> dict[str, Supplier]:
    return {supplier.supplier_id: supplier for supplier in SUPPLIERS}
