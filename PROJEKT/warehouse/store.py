from __future__ import annotations

from uuid import uuid4

from warehouse.models import (
    ProductState,
    SaleResult,
    StockAlert,
    WarehouseMetrics,
    utc_now_iso,
)


class InventoryStore:
    """Przechowuje bieżący stan magazynu."""

    def __init__(self) -> None:
        self._products: dict[str, ProductState] = {}

        # Sprzedaże, które dotarły przed snapshotem produktu.
        self._pending_sales: dict[str, list[dict]] = {}

    def apply_product_snapshot(
        self,
        event: dict,
    ) -> ProductState:
        """Dodaje nowy produkt lub aktualizuje jego dane."""

        product_id = event["product_id"]

        if product_id not in self._products:
            self._products[product_id] = ProductState(
                product_id=product_id,
                name=event["name"],
                category=event["category"],
                supplier_id=event["supplier_id"],
                price=float(event["price"]),
                reorder_level=int(event["reorder_level"]),
                current_stock=int(event["initial_stock"]),
            )
        else:
            state = self._products[product_id]

            state.name = event["name"]
            state.category = event["category"]
            state.supplier_id = event["supplier_id"]
            state.price = float(event["price"])
            state.reorder_level = int(event["reorder_level"])

        return self._products[product_id]

    def buffer_sale(
        self,
        event: dict,
    ) -> None:
        """Zapisuje sprzedaż oczekującą na dane produktu."""

        product_id = event["product_id"]

        pending = self._pending_sales.setdefault(
            product_id,
            [],
        )

        pending.append(event)

    def pop_pending_sales(
        self,
        product_id: str,
    ) -> list[dict]:
        """Pobiera i usuwa oczekujące sprzedaże produktu."""

        return self._pending_sales.pop(
            product_id,
            [],
        )

    def pending_sales_count(self) -> int:
        """Zwraca liczbę wszystkich oczekujących sprzedaży."""

        return sum(
            len(events)
            for events in self._pending_sales.values()
        )

    def apply_sale(
        self,
        event: dict,
    ) -> tuple[
        ProductState | None,
        list[StockAlert],
        SaleResult | None,
    ]:
        """Realizuje sprzedaż do wysokości dostępnego stanu."""

        product_id = event["product_id"]

        if product_id not in self._products:
            return None, [], None

        state = self._products[product_id]

        was_low_stock_before = state.is_low_stock
        was_out_of_stock_before = state.is_out_of_stock

        sale_result = state.apply_sale(
            quantity=int(event["quantity"]),
            unit_price=float(event["unit_price"]),
            event_time=event["event_time"],
        )

        alerts: list[StockAlert] = []

        # Alert może powstać tylko wtedy,
        # gdy faktycznie zmienił się stan magazynowy.
        if sale_result.was_fulfilled:
            alerts = self._generate_alerts(
                state=state,
                was_low_stock_before=was_low_stock_before,
                was_out_of_stock_before=was_out_of_stock_before,
            )

        return state, alerts, sale_result

    def _generate_alerts(
        self,
        state: ProductState,
        was_low_stock_before: bool,
        was_out_of_stock_before: bool,
    ) -> list[StockAlert]:
        """Generuje alert tylko przy przejściu do nowego stanu."""

        alerts: list[StockAlert] = []

        if (
            state.is_out_of_stock
            and not was_out_of_stock_before
        ):
            alerts.append(
                self._make_alert(
                    alert_type="out_of_stock",
                    state=state,
                )
            )

        elif (
            state.is_low_stock
            and not was_low_stock_before
        ):
            alerts.append(
                self._make_alert(
                    alert_type="low_stock",
                    state=state,
                )
            )

        return alerts

    def _make_alert(
        self,
        alert_type: str,
        state: ProductState,
    ) -> StockAlert:
        """Tworzy obiekt alertu magazynowego."""

        return StockAlert(
            alert_id=str(uuid4()),
            alert_type=alert_type,
            alert_time=utc_now_iso(),
            product_id=state.product_id,
            product_name=state.name,
            category=state.category,
            supplier_id=state.supplier_id,
            current_stock=state.current_stock,
            reorder_level=state.reorder_level,
            total_sold=state.total_sold,
            last_sale_time=state.last_sale_time,
        )

    def get_state(
        self,
        product_id: str,
    ) -> ProductState | None:
        """Zwraca stan wskazanego produktu."""

        return self._products.get(product_id)

    def all_states(self) -> list[ProductState]:
        """Zwraca stany wszystkich produktów."""

        return list(self._products.values())

    def compute_metrics(self) -> WarehouseMetrics:
        """Oblicza zbiorcze metryki magazynu."""

        states = self.all_states()

        if not states:
            return WarehouseMetrics(
                snapshot_time=utc_now_iso(),
                total_products=0,
                products_in_stock=0,
                products_low_stock=0,
                products_out_of_stock=0,
                total_stock_value=0.0,
                total_revenue=0.0,
                total_units_sold=0,
                top_selling_product_id=None,
                top_selling_product_name=None,
            )

        # Produkt jest dostępny, jeżeli ma przynajmniej jedną sztukę.
        products_in_stock = [
            state
            for state in states
            if state.current_stock > 0
        ]

        # Niski stan oznacza dodatni zapas nieprzekraczający progu.
        products_low_stock = [
            state
            for state in states
            if 0 < state.current_stock <= state.reorder_level
        ]

        # Brak towaru oznacza stan równy zero lub mniejszy.
        products_out_of_stock = [
            state
            for state in states
            if state.current_stock <= 0
        ]

        total_stock_value = sum(
            state.current_stock * state.price
            for state in states
        )

        total_revenue = sum(
            state.total_revenue
            for state in states
        )

        total_units_sold = sum(
            state.total_sold
            for state in states
        )

        top_product = max(
            states,
            key=lambda state: state.total_sold,
        )

        return WarehouseMetrics(
            snapshot_time=utc_now_iso(),
            total_products=len(states),
            products_in_stock=len(products_in_stock),
            products_low_stock=len(products_low_stock),
            products_out_of_stock=len(products_out_of_stock),
            total_stock_value=total_stock_value,
            total_revenue=total_revenue,
            total_units_sold=total_units_sold,
            top_selling_product_id=top_product.product_id,
            top_selling_product_name=top_product.name,
        )

    def state_snapshot(
        self,
        product_id: str,
    ) -> dict | None:
        """Tworzy zdarzenie z aktualnym stanem produktu."""

        state = self._products.get(product_id)

        if state is None:
            return None

        return {
            "event_type": "warehouse_state",
            "event_time": utc_now_iso(),
            "product_id": state.product_id,
            "product_name": state.name,
            "category": state.category,
            "supplier_id": state.supplier_id,
            "current_stock": state.current_stock,
            "reorder_level": state.reorder_level,
            "is_low_stock": state.is_low_stock,
            "is_out_of_stock": state.is_out_of_stock,
            "total_sold": state.total_sold,
            "total_revenue": round(
                state.total_revenue,
                2,
            ),
            "last_sale_time": state.last_sale_time,
        }
