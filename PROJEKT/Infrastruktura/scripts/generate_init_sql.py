"""Generate db/init.sql from ../data/products.json and producer/catalog.py suppliers."""

from __future__ import annotations

import json
from pathlib import Path

INFRA_ROOT = Path(__file__).resolve().parents[1]
PROJEKT_ROOT = INFRA_ROOT.parent
PRODUCTS_PATH = PROJEKT_ROOT / "data" / "products.json"
OUTPUT_PATH = INFRA_ROOT / "db" / "init.sql"

SUPPLIERS = [
    ("S001", "TechDistribution Polska", "PL", 3),
    ("S002", "EuroMonitors GmbH", "DE", 4),
    ("S003", "Nordic Accessories", "SE", 5),
    ("S004", "Storage World", "CZ", 2),
    ("S005", "Network Partner", "PL", 3),
    ("S006", "Mobile Europe", "NL", 6),
    ("S007", "Audio Premium", "JP", 8),
]


def esc(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    lines = [
        "-- RTA warehouse project — PostgreSQL seed from PROJEKT/data/products.json",
        "",
        "CREATE TABLE IF NOT EXISTS suppliers (",
        "    supplier_id VARCHAR(8) PRIMARY KEY,",
        "    name VARCHAR(255) NOT NULL,",
        "    country VARCHAR(8) NOT NULL,",
        "    average_delivery_days INTEGER NOT NULL,",
        "    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS products (",
        "    product_id VARCHAR(8) PRIMARY KEY,",
        "    name VARCHAR(255) NOT NULL,",
        "    category VARCHAR(64) NOT NULL,",
        "    price NUMERIC(12, 2) NOT NULL,",
        "    supplier_id VARCHAR(8) NOT NULL REFERENCES suppliers (supplier_id),",
        "    reorder_level INTEGER NOT NULL,",
        "    initial_stock INTEGER NOT NULL,",
        "    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS inventory_snapshots (",
        "    id BIGSERIAL PRIMARY KEY,",
        "    product_id VARCHAR(8) NOT NULL REFERENCES products (product_id),",
        "    quantity_on_hand INTEGER NOT NULL,",
        "    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        ");",
        "",
        "CREATE INDEX IF NOT EXISTS idx_products_supplier ON products (supplier_id);",
        "CREATE INDEX IF NOT EXISTS idx_inventory_product_recorded ON inventory_snapshots (product_id, recorded_at DESC);",
        "",
        "INSERT INTO suppliers (supplier_id, name, country, average_delivery_days) VALUES",
    ]

    supplier_rows = [
        f"    ('{sid}', '{esc(name)}', '{country}', {days})"
        for sid, name, country, days in SUPPLIERS
    ]
    lines.append(",\n".join(supplier_rows))
    lines.append("ON CONFLICT (supplier_id) DO NOTHING;")
    lines.append("")
    lines.append(
        "INSERT INTO products (product_id, name, category, price, supplier_id, reorder_level, initial_stock) VALUES"
    )

    product_rows = [
        (
            f"    ('{p['product_id']}', '{esc(p['name'])}', '{p['category']}', "
            f"{p['price']}, '{p['supplier_id']}', {p['reorder_level']}, {p['initial_stock']})"
        )
        for p in products
    ]
    lines.append(",\n".join(product_rows))
    lines.append("ON CONFLICT (product_id) DO NOTHING;")
    lines.append("")
    lines.append("INSERT INTO inventory_snapshots (product_id, quantity_on_hand) VALUES")

    inventory_rows = [
        f"    ('{p['product_id']}', {p['initial_stock']})" for p in products
    ]
    lines.append(",\n".join(inventory_rows))
    lines.append(";")

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(products)} products, {len(SUPPLIERS)} suppliers)")


if __name__ == "__main__":
    main()
