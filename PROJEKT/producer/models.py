from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    price: float
    supplier_id: str
    initial_stock: int
    reorder_level: int

    def to_event(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_id"] = str(uuid4())
        data["event_type"] = "product_snapshot"
        data["event_time"] = utc_now_iso()
        return data


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    name: str
    country: str
    average_delivery_days: int

    def to_event(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_id"] = str(uuid4())
        data["event_type"] = "supplier_snapshot"
        data["event_time"] = utc_now_iso()
        return data


@dataclass(frozen=True)
class TopicNames:
    products: str = "products"
    suppliers: str = "suppliers"
    sales: str = "sales"
