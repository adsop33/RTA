# Kafka i infrastruktura

Moduł infrastruktury projektu magazynowego RTA — Apache Kafka, Docker Compose, PostgreSQL, Redis i środowisko JupyterLab.

Wszystkie pliki modułu znajdują się w katalogu `PROJEKT/Infrastruktura/`.

---

## Struktura

```text
PROJEKT/Infrastruktura/
├── compose.yaml              # Docker Compose stack
├── Dockerfile                # JupyterLab + Kafka CLI + biblioteki Python
├── requirements.txt
├── .env.example
├── create_topics.py          # Ręczne tworzenie topików Kafka
├── db/init.sql               # PostgreSQL — seed z ../data/products.json
├── kafka/init-topics.sh      # Automatyczne tworzenie topików przy starcie
├── scripts/
│   ├── healthcheck.sh
│   └── generate_init_sql.py
└── Kafka i infrastruktura.md
```

---

## Uruchomienie

```powershell
cd C:\Users\miryd\Projects\RTA\PROJEKT\Infrastruktura
copy .env.example .env
docker compose up -d --build
```

| Usługa | Adres |
|--------|-------|
| JupyterLab | http://localhost:8999 (token: `root`) |
| Kafka (z hosta Windows) | `localhost:29092` |
| Kafka (w Jupyter / Docker) | `broker:9092` |
| PostgreSQL | `localhost:5432` / user `rta` / db `rta` |
| Redis | `localhost:6379` |

Katalog roboczy w JupyterLab: `/home/jovyan/notebooks/PROJEKT` (moduły `producer`, `warehouse` itd.).

### Zatrzymanie

```powershell
docker compose down
```

### Reset bazy

```powershell
docker compose down -v
docker compose up -d --build
```

---

## Topiki Kafka

Zgodne z modułami `producer`, `warehouse`, `purchase_orders`, `modelowanie/predykcja`:

| Topik | Używany przez |
|-------|---------------|
| `products` | producer → warehouse, purchase_orders |
| `suppliers` | producer → purchase_orders |
| `sales` | producer → warehouse, predykcja |
| `warehouse_states` | warehouse → purchase_orders |
| `warehouse_alerts` | warehouse |
| `warehouse_metrics` | warehouse |
| `sales_forecasts` | modelowanie |
| `purchase_orders` | purchase_orders |
| `deliveries` | modelowanie/predykcja |

Tworzone automatycznie przez `kafka-init`. Ręcznie:

```bash
cd Infrastruktura
python create_topics.py --bootstrap-servers broker:9092
```

---

## PostgreSQL

- Seed: 7 dostawców + 30 produktów z `../data/products.json`
- Regeneracja po zmianie danych:

```bash
python scripts/generate_init_sql.py
```

---

## Uruchomienie modułów aplikacji

W JupyterLab (katalog `PROJEKT`):

```bash
python -m purchase_orders.main --bootstrap-servers broker:9092 --flush-seconds 3 --verbose
python -m warehouse.main --bootstrap-servers broker:9092 --metrics-every 10 --verbose
python -m producer.main --bootstrap-servers broker:9092 --scenario demand_spike --events 50 --interval 0.2
```

---

## Weryfikacja

```bash
bash Infrastruktura/scripts/healthcheck.sh
kafka-topics.sh --list --bootstrap-server broker:9092
```

Oczekiwane: 9 topików, 30 produktów w PostgreSQL.
