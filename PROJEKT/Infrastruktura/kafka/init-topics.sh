#!/bin/bash
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP:-broker:9092}"
MAX_RETRIES=30
RETRY_DELAY=2

echo "Waiting for Kafka broker at ${BOOTSTRAP}..."
for i in $(seq 1 $MAX_RETRIES); do
  if kafka-broker-api-versions --bootstrap-server "${BOOTSTRAP}" >/dev/null 2>&1; then
    echo "Broker is ready."
    break
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "Broker not ready after ${MAX_RETRIES} attempts." >&2
    exit 1
  fi
  sleep "${RETRY_DELAY}"
done

create_topic() {
  local topic="$1"
  local partitions="$2"
  if kafka-topics --bootstrap-server "${BOOTSTRAP}" --list | grep -qx "${topic}"; then
    echo "Topic already exists: ${topic}"
  else
    kafka-topics --create \
      --topic "${topic}" \
      --bootstrap-server "${BOOTSTRAP}" \
      --partitions "${partitions}" \
      --replication-factor 1
    echo "Created topic: ${topic} (${partitions} partitions)"
  fi
}

# Topiki zgodne z PROJEKT/purchase_orders/create_topics.py i modułami aplikacji
create_topic "products" 1
create_topic "suppliers" 1
create_topic "sales" 1
create_topic "warehouse_states" 1
create_topic "warehouse_alerts" 1
create_topic "warehouse_metrics" 1
create_topic "sales_forecasts" 1
create_topic "purchase_orders" 1
create_topic "deliveries" 1

echo "All topics ready:"
kafka-topics --bootstrap-server "${BOOTSTRAP}" --list
