from __future__ import annotations

from typing import Any

from purchase_orders.models import (
    ProductInfo,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierInfo,
    WarehouseState,
)


class PurchaseOrderStore:
    """Przechowuje dane potrzebne do tworzenia zleceń zakupu."""

    def __init__(self) -> None:
        self._products: dict[str, ProductInfo] = {}
        self._suppliers: dict[str, SupplierInfo] = {}
        self._warehouse_states: dict[str, WarehouseState] = {}

        # Produkty oczekujące na zebranie do zamówienia,
        # pogrupowane według dostawcy.
        self._pending_items: dict[
            str,
            dict[str, PurchaseOrderItem],
        ] = {}

        # Produkty, dla których opublikowano już zamówienie.
        self._ordered_products: set[str] = set()

    def apply_product_snapshot(
        self,
        event: dict[str, Any],
    ) -> ProductInfo:
        product = ProductInfo.from_event(event)
        self._products[product.product_id] = product
        return product

    def apply_supplier_snapshot(
        self,
        event: dict[str, Any],
    ) -> SupplierInfo:
        supplier = SupplierInfo.from_event(event)
        self._suppliers[supplier.supplier_id] = supplier
        return supplier

    def apply_warehouse_state(
        self,
        event: dict[str, Any],
    ) -> WarehouseState:
        state = WarehouseState.from_event(event)
        self._warehouse_states[state.product_id] = state
        return state

    def get_product(
        self,
        product_id: str,
    ) -> ProductInfo | None:
        return self._products.get(product_id)

    def get_supplier(
        self,
        supplier_id: str,
    ) -> SupplierInfo | None:
        return self._suppliers.get(supplier_id)

    def get_warehouse_state(
        self,
        product_id: str,
    ) -> WarehouseState | None:
        return self._warehouse_states.get(product_id)

    def is_already_ordered(
        self,
        product_id: str,
    ) -> bool:
        return product_id in self._ordered_products

    def calculate_order_quantity(
        self,
        state: WarehouseState,
    ) -> int:
        """
        Minimalna reguła zamawiania:

        stan docelowy = dwukrotność progu zamówienia
        ilość zamówienia = stan docelowy - stan obecny
        """

        target_stock = state.reorder_level * 2

        return max(
            0,
            target_stock - state.current_stock,
        )

    def queue_product_if_needed(
        self,
        product_id: str,
    ) -> bool:
        """
        Dodaje produkt do oczekującego zamówienia,
        jeżeli jego stan jest niski.

        Zwraca True tylko wtedy, gdy produkt został
        dodany do bufora po raz pierwszy.

        Jeżeli produkt już znajduje się w buforze,
        jego pozycja jest aktualizowana, ale metoda
        zwraca False.
        """

        product = self.get_product(product_id)
        state = self.get_warehouse_state(product_id)

        if product is None or state is None:
            return False

        if not state.is_low_stock:
            return False

        if self.is_already_ordered(product_id):
            return False

        quantity = self.calculate_order_quantity(state)

        if quantity <= 0:
            return False

        item = PurchaseOrderItem(
            product_id=product.product_id,
            product_name=product.name,
            current_stock=state.current_stock,
            reorder_level=state.reorder_level,
            quantity=quantity,
        )

        supplier_items = self._pending_items.setdefault(
            product.supplier_id,
            {},
        )

        was_already_pending = (
            product.product_id in supplier_items
        )

        # Zapisujemy najnowszą pozycję na podstawie
        # aktualnego stanu magazynowego.
        supplier_items[product.product_id] = item

        # True oznacza rzeczywiste pierwsze dodanie.
        # False oznacza jedynie aktualizację istniejącej pozycji.
        return not was_already_pending

    def pending_supplier_ids(self) -> list[str]:
        """Zwraca dostawców mających oczekujące pozycje."""

        return [
            supplier_id
            for supplier_id, items
            in self._pending_items.items()
            if items
        ]

    def create_order_for_supplier(
        self,
        supplier_id: str,
    ) -> PurchaseOrder | None:
        """
        Tworzy zbiorcze zamówienie dla jednego dostawcy.
        Nie usuwa jeszcze pozycji z bufora.
        """

        supplier = self.get_supplier(supplier_id)
        pending = self._pending_items.get(supplier_id)

        if supplier is None or not pending:
            return None

        return PurchaseOrder.create(
            supplier=supplier,
            items=list(pending.values()),
        )

    def mark_order_as_published(
        self,
        order: PurchaseOrder,
    ) -> None:
        """
        Oznacza produkty jako zamówione i usuwa
        opublikowane pozycje z bufora.
        """

        for item in order.items:
            self._ordered_products.add(
                item.product_id
            )

        self._pending_items.pop(
            order.supplier_id,
            None,
        )

    def pending_items_count(self) -> int:
        """Zwraca liczbę pozycji oczekujących w buforze."""

        return sum(
            len(items)
            for items in self._pending_items.values()
        )
