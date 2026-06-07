from __future__ import annotations

import argparse
import logging
import signal
import time

from purchase_orders.kafka_io import (
    ConsolePurchaseOrderProducer,
    PurchaseOrderConsumer,
    PurchaseOrderProducer,
)
from purchase_orders.store import PurchaseOrderStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logging.getLogger("kafka").setLevel(logging.WARNING)

log = logging.getLogger("purchase-orders")

PURCHASE_ORDERS_TOPIC = "purchase_orders"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Moduł tworzenia zleceń zakupu."
    )

    parser.add_argument(
        "--bootstrap-servers",
        default="broker:9092",
        help="Adres brokera Kafka.",
    )

    parser.add_argument(
        "--flush-seconds",
        type=float,
        default=5.0,
        help=(
            "Liczba sekund przeznaczona na zebranie produktów "
            "do zbiorczego zamówienia."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Wypisuje zamówienia zamiast wysyłać je do Kafki.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Wyświetla informacje o odebranych zdarzeniach.",
    )

    return parser.parse_args()


def publish_pending_orders(
    store: PurchaseOrderStore,
    producer: PurchaseOrderProducer | ConsolePurchaseOrderProducer,
) -> int:
    """
    Tworzy i publikuje po jednym zbiorczym zamówieniu
    dla każdego dostawcy.
    """

    published = 0

    for supplier_id in store.pending_supplier_ids():
        order = store.create_order_for_supplier(
            supplier_id
        )

        if order is None:
            log.warning(
                "Nie można utworzyć zamówienia dla dostawcy %s. "
                "Brak danych dostawcy lub pozycji zamówienia.",
                supplier_id,
            )
            continue

        producer.send(
            topic=PURCHASE_ORDERS_TOPIC,
            key=order.supplier_id,
            value=order.to_event(),
        )

        store.mark_order_as_published(order)
        published += 1

        log.warning(
            "UTWORZONO ZAMÓWIENIE %s | "
            "dostawca: %s (%s) | "
            "pozycje: %d | sztuki: %d",
            order.order_id,
            order.supplier_name,
            order.supplier_id,
            order.total_items,
            order.total_quantity,
        )

        for item in order.items:
            log.info(
                "  %s (%s) | stan: %d | próg: %d | "
                "zamówiono: %d",
                item.product_name,
                item.product_id,
                item.current_stock,
                item.reorder_level,
                item.quantity,
            )

    if published > 0:
        producer.flush()

    return published


def run(args: argparse.Namespace) -> None:
    store = PurchaseOrderStore()

    consumer = PurchaseOrderConsumer(
        args.bootstrap_servers
    )

    if args.dry_run:
        producer = ConsolePurchaseOrderProducer()

        log.info(
            "Tryb dry-run: zamówienia będą wypisywane "
            "zamiast wysyłania do Kafki."
        )
    else:
        producer = PurchaseOrderProducer(
            args.bootstrap_servers
        )

    processed_events = 0
    published_orders = 0

    pending_since: float | None = None

    def try_queue_product(product_id: str) -> bool:
        """
        Sprawdza, czy produkt powinien zostać dodany
        do oczekującego zamówienia.

        Funkcja działa niezależnie od tego, czy najpierw
        dotarł produkt, czy stan magazynowy.
        """

        nonlocal pending_since

        added = store.queue_product_if_needed(
            product_id
        )

        if added:
            log.warning(
                "Dodano produkt %s do oczekującego zamówienia",
                product_id,
            )

            if pending_since is None:
                pending_since = time.monotonic()

        return added

    def shutdown(signum, frame) -> None:
        log.info(
            "Otrzymano sygnał zakończenia."
        )

        raise KeyboardInterrupt

    signal.signal(
        signal.SIGTERM,
        shutdown,
    )

    log.info(
        "Uruchamiam moduł zleceń zakupu: %s",
        args.bootstrap_servers,
    )

    log.info(
        "Oczekuję na topiki: "
        "products, suppliers, warehouse_states"
    )

    try:
        for topic, event in consumer.poll_events():

            if topic is not None and event is not None:
                processed_events += 1

                if (
                    topic == "products"
                    and event.get("event_type") == "product_snapshot"
                ):
                    product = store.apply_product_snapshot(
                        event
                    )

                    if args.verbose:
                        log.info(
                            "Produkt: %s (%s), dostawca: %s",
                            product.name,
                            product.product_id,
                            product.supplier_id,
                        )

                    try_queue_product(
                        product.product_id
                    )

                elif (
                    topic == "suppliers"
                    and event.get("event_type") == "supplier_snapshot"
                ):
                    supplier = store.apply_supplier_snapshot(
                        event
                    )

                    if args.verbose:
                        log.info(
                            "Dostawca: %s (%s), dostawa: %d dni",
                            supplier.name,
                            supplier.supplier_id,
                            supplier.average_delivery_days,
                        )

                elif (
                    topic == "warehouse_states"
                    and event.get("event_type") == "warehouse_state"
                ):
                    state = store.apply_warehouse_state(
                        event
                    )

                    if args.verbose:
                        log.info(
                            "Stan: %s | ilość: %d | "
                            "próg: %d | niski: %s",
                            state.product_id,
                            state.current_stock,
                            state.reorder_level,
                            state.is_low_stock,
                        )

                    try_queue_product(
                        state.product_id
                    )

                else:
                    log.debug(
                        "Pominięto zdarzenie: topic=%s, type=%s",
                        topic,
                        event.get("event_type"),
                    )

            current_time = time.monotonic()

            if (
                pending_since is not None
                and store.pending_items_count() > 0
                and current_time - pending_since
                >= args.flush_seconds
            ):
                published_orders += publish_pending_orders(
                    store,
                    producer,
                )

                if store.pending_items_count() == 0:
                    pending_since = None
                else:
                    pending_since = current_time

    except KeyboardInterrupt:
        log.info(
            "Przerwano działanie modułu."
        )

    finally:
        published_orders += publish_pending_orders(
            store,
            producer,
        )

        consumer.close()
        producer.close()

        log.info(
            "=== PODSUMOWANIE ==="
        )

        log.info(
            "Przetworzone zdarzenia: %d",
            processed_events,
        )

        log.info(
            "Opublikowane zamówienia: %d",
            published_orders,
        )


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()