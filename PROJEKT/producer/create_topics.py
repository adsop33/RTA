from __future__ import annotations

import argparse

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from producer.models import TopicNames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tworzy topiki Kafka wymagane przez producenta.")
    parser.add_argument("--bootstrap-servers", default="broker:9092")
    parser.add_argument("--partitions", type=int, default=1)
    parser.add_argument("--replication-factor", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topics = TopicNames()
    topic_names = [
        topics.products,
        topics.suppliers,
        topics.sales,
    ]

    admin = KafkaAdminClient(
        bootstrap_servers=args.bootstrap_servers,
        client_id="producer-topic-setup",
    )

    try:
        existing_topics = set(admin.list_topics())
        new_topics = [
            NewTopic(
                name=topic_name,
                num_partitions=args.partitions,
                replication_factor=args.replication_factor,
            )
            for topic_name in topic_names
            if topic_name not in existing_topics
        ]

        if new_topics:
            admin.create_topics(new_topics=new_topics, validate_only=False)
            print("Utworzono topiki:", ", ".join(topic.name for topic in new_topics))
        else:
            print("Wszystkie topiki juz istnieja.")

        print("Aktualne topiki projektu:", ", ".join(topic_names))
    except TopicAlreadyExistsError:
        print("Czesc topikow juz istniala. Mozesz kontynuowac.")
    finally:
        admin.close()


if __name__ == "__main__":
    main()
