from __future__ import annotations

import json
from typing import Iterator

try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError:
    KafkaConsumer = None
    KafkaProducer = None


class PurchaseOrderConsumer:
    """Odbiera dane potrzebne do tworzenia zamówień."""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str = "purchase-order-processor",
    ) -> None:
        if KafkaConsumer is None:
            raise RuntimeError(
                "Brak biblioteki kafka-python. "
                "Zainstaluj ją poleceniem: pip install kafka-python"
            )

        self._consumer = KafkaConsumer(
            "products",
            "suppliers",
            "warehouse_states",
            bootstrap_servers=bootstrap_servers.split(","),
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            key_deserializer=(
                lambda value: value.decode("utf-8")
                if value
                else None
            ),
            value_deserializer=(
                lambda value: json.loads(
                    value.decode("utf-8")
                )
            ),
            consumer_timeout_ms=-1,
        )

    def poll_events(
        self,
        timeout_ms: int = 500,
    ) -> Iterator[tuple[str | None, dict | None]]:
        """
        Odbiera wiadomości z Kafki.
    
        Gdy przez określony czas nie ma nowych wiadomości,
        zwraca (None, None). Dzięki temu główna pętla może
        okresowo sprawdzać, czy należy opublikować zamówienia.
        """
    
        while True:
            batches = self._consumer.poll(
                timeout_ms=timeout_ms,
            )
    
            if not batches:
                yield None, None
                continue
    
            for messages in batches.values():
                for message in messages:
                    yield message.topic, message.value

    def close(self) -> None:
        self._consumer.close()


class PurchaseOrderProducer:
    """Wysyła gotowe zlecenia do topiku purchase_orders."""

    def __init__(self, bootstrap_servers: str) -> None:
        if KafkaProducer is None:
            raise RuntimeError(
                "Brak biblioteki kafka-python. "
                "Zainstaluj ją poleceniem: pip install kafka-python"
            )

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            key_serializer=(
                lambda value: value.encode("utf-8")
            ),
            value_serializer=(
                lambda value: json.dumps(
                    value,
                    ensure_ascii=False,
                ).encode("utf-8")
            ),
            acks="all",
            retries=3,
        )

    def send(
        self,
        topic: str,
        key: str,
        value: dict,
    ) -> None:
        self._producer.send(
            topic,
            key=key,
            value=value,
        )

    def flush(self) -> None:
        self._producer.flush()

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()


class ConsolePurchaseOrderProducer:
    """Tryb testowy: wypisuje zamówienia zamiast wysyłać do Kafki."""

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