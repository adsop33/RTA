from __future__ import annotations

import json
from typing import Protocol

try:
    from kafka import KafkaProducer
except ImportError:  # pragma: no cover - handled at runtime for dry-run mode.
    KafkaProducer = None


class EventPublisher(Protocol):
    def publish(self, topic: str, key: str, event: dict) -> None:
        ...

    def close(self) -> None:
        ...


class ConsolePublisher:
    def publish(self, topic: str, key: str, event: dict) -> None:
        payload = json.dumps(event, ensure_ascii=False)
        print(f"[dry-run] topic={topic} key={key} event={payload}")

    def close(self) -> None:
        return None


class PrintingPublisher:
    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher

    def publish(self, topic: str, key: str, event: dict) -> None:
        payload = json.dumps(event, ensure_ascii=False)
        print(f"[sent] topic={topic} key={key} event={payload}")
        self._publisher.publish(topic, key, event)

    def close(self) -> None:
        self._publisher.close()


class KafkaEventPublisher:
    def __init__(self, bootstrap_servers: str) -> None:
        if KafkaProducer is None:
            raise RuntimeError(
                "Brak biblioteki kafka-python. Zainstaluj zaleznosci: pip install -r requirements.txt"
            )

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            key_serializer=lambda value: value.encode("utf-8"),
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
            acks="all",
            retries=3,
        )

    def publish(self, topic: str, key: str, event: dict) -> None:
        self._producer.send(topic, key=key, value=event)

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()
