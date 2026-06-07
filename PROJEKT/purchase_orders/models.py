from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    """Zwraca aktualny czas UTC w formacie ISO."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ProductInfo:
    """Podstawowe dane produktu otrzymane z topiku products."""

    product_id: str
    name: str
    category: str
    supplier_id: str
    price: float
    reorder_level: int

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> ProductInfo:
        return cls(
            product_id=event["product_id"],
            name=event["name"],
            category=event["category"],
            supplier_id=event["supplier_id"],
            price=float(event["price"]),
            reorder_level=int(event["reorder_level"]),
        )


@dataclass(frozen=True)
class SupplierInfo:
    """Dane dostawcy otrzymane z topiku suppliers."""

    supplier_id: str
    name: str
    country: str
    average_delivery_days: int

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> SupplierInfo:
        return cls(
            supplier_id=event["supplier_id"],
            name=event["name"],
            country=event["country"],
            average_delivery_days=int(event["average_delivery_days"]),
        )


@dataclass(frozen=True)
class WarehouseState:
    """Aktualny stan produktu otrzymany z topiku warehouse_states."""

    product_id: str
    supplier_id: str
    current_stock: int
    reorder_level: int
    is_low_stock: bool
    is_out_of_stock: bool
    event_time: str

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> WarehouseState:
        return cls(
            product_id=event["product_id"],
            supplier_id=event["supplier_id"],
            current_stock=int(event["current_stock"]),
            reorder_level=int(event["reorder_level"]),
            is_low_stock=bool(event["is_low_stock"]),
            is_out_of_stock=bool(event["is_out_of_stock"]),
            event_time=event["event_time"],
        )


@dataclass(frozen=True)
class PurchaseOrderItem:
    """Jedna pozycja na zleceniu zakupu."""

    product_id: str
    product_name: str
    current_stock: int
    reorder_level: int
    quantity: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PurchaseOrder:
    """Zbiorcze zlecenie zakupu dla jednego dostawcy."""

    event_id: str
    order_id: str
    event_time: str
    supplier_id: str
    supplier_name: str
    supplier_country: str
    average_delivery_days: int
    status: str
    items: tuple[PurchaseOrderItem, ...]

    @classmethod
    def create(
        cls,
        supplier: SupplierInfo,
        items: list[PurchaseOrderItem],
    ) -> PurchaseOrder:
        return cls(
            event_id=str(uuid4()),
            order_id=f"PO-{uuid4().hex[:12].upper()}",
            event_time=utc_now_iso(),
            supplier_id=supplier.supplier_id,
            supplier_name=supplier.name,
            supplier_country=supplier.country,
            average_delivery_days=supplier.average_delivery_days,
            status="created",
            items=tuple(items),
        )

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def total_items(self) -> int:
        return len(self.items)

    def to_event(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": "purchase_order",
            "event_time": self.event_time,
            "order_id": self.order_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "supplier_country": self.supplier_country,
            "average_delivery_days": self.average_delivery_days,
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
            "total_items": self.total_items,
            "total_quantity": self.total_quantity,
        }