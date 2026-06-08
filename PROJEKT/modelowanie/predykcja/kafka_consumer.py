import json
from kafka import KafkaConsumer


class KafkaEventConsumer:

    def __init__(self, config):

        self.consumer = KafkaConsumer(
            config.SALES_TOPIC,
            config.DELIVERIES_TOPIC,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True
        )

    def listen(self):
        for message in self.consumer:
            yield message.topic, message.value