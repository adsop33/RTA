from __future__ import annotations

import argparse

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError


TOPICS = [
    "products",
    "suppliers",
    "sales",
    "warehouse_states",
    "warehouse_alerts",
    "warehouse_metrics",
    "sales_forecasts",
    "purchase_orders",
    "deliveries",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tworzy topiki Kafka dla systemu zarządzania magazynem."
    )
    parser.add_argument(
        "--bootstrap-servers",
        default="broker:9092",
    )
    parser.add_argument(
        "--partitions",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--replication-factor",
        type=int,
        default=1,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    admin = KafkaAdminClient(
        bootstrap_servers=args.bootstrap_servers.split(","),
        client_id="warehouse-topic-setup",
    )

    try:
        existing_topics = set(admin.list_topics())

        topics_to_create = [
            NewTopic(
                name=topic_name,
                num_partitions=args.partitions,
                replication_factor=args.replication_factor,
            )
            for topic_name in TOPICS
            if topic_name not in existing_topics
        ]

        if topics_to_create:
            admin.create_topics(
                new_topics=topics_to_create,
                validate_only=False,
            )

            print("Utworzono topiki:")
            for topic in topics_to_create:
                print(f"  - {topic.name}")
        else:
            print("Wszystkie wymagane topiki już istnieją.")

        print("\nTopiki używane w projekcie:")
        for topic_name in TOPICS:
            print(f"  - {topic_name}")

    except TopicAlreadyExistsError:
        print("Część topików już istniała.")

    finally:
        admin.close()


if __name__ == "__main__":
    main()