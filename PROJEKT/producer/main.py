from __future__ import annotations

import argparse
import time
from pathlib import Path

from producer.catalog import load_products
from producer.generator import EventGenerator, Scenario
from producer.kafka_io import ConsolePublisher, EventPublisher, KafkaEventPublisher, PrintingPublisher
from producer.models import TopicNames


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS_PATH = ROOT_DIR / "data" / "products.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generator zdarzen i producent Kafka.")
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--products-file", type=Path, default=DEFAULT_PRODUCTS_PATH)
    parser.add_argument(
        "--scenario",
        choices=["normal", "demand_spike"],
        default="normal",
    )
    parser.add_argument("--interval", type=float, default=1.0, help="Przerwa miedzy zdarzeniami.")
    parser.add_argument("--events", type=int, default=0, help="Liczba zdarzen. 0 oznacza bez konca.")
    parser.add_argument("--dry-run", action="store_true", help="Wypisuje zdarzenia zamiast wysylac do Kafka.")
    parser.add_argument(
        "--print-events",
        action="store_true",
        help="Wypisuje zdarzenia wysylane do Kafka.",
    )
    return parser.parse_args()


def create_publisher(args: argparse.Namespace) -> EventPublisher:
    if args.dry_run:
        return ConsolePublisher()

    publisher: EventPublisher = KafkaEventPublisher(args.bootstrap_servers)
    if args.print_events:
        return PrintingPublisher(publisher)
    return publisher


def publish_bootstrap_events(generator: EventGenerator, publisher: EventPublisher, topics: TopicNames) -> None:
    for _, key, event in generator.product_events():
        publisher.publish(topics.products, key, event)

    for _, key, event in generator.supplier_events():
        publisher.publish(topics.suppliers, key, event)


def main() -> None:
    args = parse_args()
    topics = TopicNames()
    products = load_products(args.products_file)
    generator = EventGenerator(products, args.scenario)
    publisher = create_publisher(args)

    try:
        publish_bootstrap_events(generator, publisher, topics)
        sent = 0

        while args.events == 0 or sent < args.events:
            _, key, event = generator.next_sale()
            publisher.publish(topics.sales, key, event)
            sent += 1
            time.sleep(args.interval)
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
