from __future__ import annotations

import argparse
import json
import logging
import signal

from warehouse.kafka_io import WarehouseConsumer, WarehouseProducer
from warehouse.models import TopicNames
from warehouse.store import InventoryStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logging.getLogger("kafka").setLevel(logging.WARNING)

log = logging.getLogger("warehouse")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Procesor magazynu – konsument Kafka."
    )

    parser.add_argument(
        "--bootstrap-servers",
        default="broker:9092",
        help="Adres brokera Kafka.",
    )

    parser.add_argument(
        "--metrics-every",
        type=int,
        default=10,
        help=(
            "Co ile zdarzeń sprzedaży publikować metryki "
            "(domyślnie: 10)."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Wypisuje zdarzenia wynikowe na konsolę "
            "zamiast wysyłać je do Kafki."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Wypisuje każde przetworzone zdarzenie sprzedaży.",
    )

    return parser.parse_args()


class ConsoleProducer:
    """Producent testowy wypisujący zdarzenia na konsolę."""

    def send(
        self,
        topic: str,
        key: str,
        value: dict,
    ) -> None:
        payload = json.dumps(
            value,
            ensure_ascii=False,
        )

        print(
            f"[dry-run] topic={topic} "
            f"key={key} | {payload}"
        )

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


def run(args: argparse.Namespace) -> None:
    topics = TopicNames()
    store = InventoryStore()

    # Liczba przetworzonych zdarzeń sprzedaży.
    # Obejmuje również sprzedaże częściowe i niezrealizowane.
    sales_processed = 0
    lost_demand_units = 0

    if args.dry_run:
        publisher = ConsoleProducer()

        log.info(
            "Tryb dry-run: zdarzenia wynikowe będą "
            "wypisywane na konsolę."
        )
    else:
        publisher = WarehouseProducer(
            args.bootstrap_servers
        )

    consumer = WarehouseConsumer(
        args.bootstrap_servers
    )

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
        "Uruchamiam konsumenta Kafka: %s",
        args.bootstrap_servers,
    )

    log.info(
        "Oczekuję na zdarzenia z topików: products, sales ..."
    )

    try:
        for topic, event in consumer.poll_events():

            if (
                topic == topics.products
                and event.get("event_type") == "product_snapshot"
            ):
                store.apply_product_snapshot(event)

                log.debug(
                    "Zarejestrowano produkt: %s",
                    event.get("product_id"),
                )

            elif (
                topic == topics.sales
                and event.get("event_type") == "sale"
            ):
                state, alerts, sale_result = store.apply_sale(
                    event
                )

                if state is None or sale_result is None:
                    log.warning(
                        "Nieznany produkt w zdarzeniu sprzedaży: %s",
                        event.get("product_id"),
                    )
                    continue

                sales_processed += 1
                lost_demand_units += (
                    sale_result.unfulfilled_quantity
                )

                # Stan publikujemy tylko wtedy,
                # gdy faktycznie wydano przynajmniej jedną sztukę.
                if sale_result.was_fulfilled:
                    snapshot = store.state_snapshot(
                        state.product_id
                    )

                    if snapshot is not None:
                        publisher.send(
                            topics.warehouse_states,
                            state.product_id,
                            snapshot,
                        )

                if sale_result.was_rejected:
                    log.warning(
                        "NIEZREALIZOWANA SPRZEDAŻ: %s (%s) | "
                        "żądano: %d | zrealizowano: 0 | "
                        "brak: %d | stan: %d",
                        state.name,
                        state.product_id,
                        sale_result.requested_quantity,
                        sale_result.unfulfilled_quantity,
                        state.current_stock,
                    )

                elif sale_result.was_partially_fulfilled:
                    log.warning(
                        "CZĘŚCIOWA SPRZEDAŻ: %s (%s) | "
                        "żądano: %d | zrealizowano: %d | "
                        "brak: %d | przychód: %.2f PLN | "
                        "stan: %d",
                        state.name,
                        state.product_id,
                        sale_result.requested_quantity,
                        sale_result.fulfilled_quantity,
                        sale_result.unfulfilled_quantity,
                        sale_result.fulfilled_amount,
                        state.current_stock,
                    )

                elif args.verbose:
                    log.info(
                        "Sprzedaż: %s (%s) | "
                        "zrealizowano: %d | "
                        "przychód: %.2f PLN | "
                        "stan: %d (próg: %d)",
                        state.name,
                        state.product_id,
                        sale_result.fulfilled_quantity,
                        sale_result.fulfilled_amount,
                        state.current_stock,
                        state.reorder_level,
                    )

                for alert in alerts:
                    publisher.send(
                        topics.warehouse_alerts,
                        alert.product_id,
                        alert.to_dict(),
                    )

                    log.warning(
                        "ALERT [%s] %s (%s) – "
                        "stan: %d / próg: %d",
                        alert.alert_type.upper(),
                        alert.product_name,
                        alert.product_id,
                        alert.current_stock,
                        alert.reorder_level,
                    )

                if (
                    sales_processed
                    % args.metrics_every
                    == 0
                ):
                    metrics = store.compute_metrics()

                    publisher.send(
                        topics.warehouse_metrics,
                        "global",
                        metrics.to_dict(),
                    )

                    publisher.flush()

                    log.info(
                        "Metryki [%d zdarzeń sprzedaży] | "
                        "produkty: %d | na stanie: %d | "
                        "niski stan: %d | wyczerpane: %d | "
                        "sprzedane sztuki: %d | "
                        "utracony popyt: %d | "
                        "przychód: %.2f PLN",
                        sales_processed,
                        metrics.total_products,
                        metrics.products_in_stock,
                        metrics.products_low_stock,
                        metrics.products_out_of_stock,
                        metrics.total_units_sold,
                        lost_demand_units,
                        metrics.total_revenue,
                    )

            else:
                log.debug(
                    "Pominięto zdarzenie: topic=%s, type=%s",
                    topic,
                    event.get("event_type"),
                )

    except KeyboardInterrupt:
        log.info(
            "Przerwano działanie modułu."
        )

    finally:
        consumer.close()
        publisher.close()

        metrics = store.compute_metrics()

        log.info(
            "Zamknięto konsumenta i producenta."
        )

        log.info(
            "=== PODSUMOWANIE ==="
        )

        log.info(
            "Przetworzone zdarzenia sprzedaży: %d",
            sales_processed,
        )

        log.info(
            "Faktycznie sprzedane sztuki: %d",
            metrics.total_units_sold,
        )

        log.info(
            "Utracony popyt: %d sztuk",
            lost_demand_units,
        )

        log.info(
            "Produkty na stanie: %d",
            metrics.products_in_stock,
        )

        log.info(
            "Produkty z niskim stanem: %d",
            metrics.products_low_stock,
        )

        log.info(
            "Produkty wyczerpane: %d",
            metrics.products_out_of_stock,
        )

        log.info(
            "Łączny rzeczywisty przychód: %.2f PLN",
            metrics.total_revenue,
        )

        if metrics.top_selling_product_name:
            log.info(
                "Najlepiej sprzedający się produkt: %s",
                metrics.top_selling_product_name,
            )


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()