-- RTA warehouse project — PostgreSQL seed from PROJEKT/data/products.json

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(8) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(8) NOT NULL,
    average_delivery_days INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(8) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    supplier_id VARCHAR(8) NOT NULL REFERENCES suppliers (supplier_id),
    reorder_level INTEGER NOT NULL,
    initial_stock INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id BIGSERIAL PRIMARY KEY,
    product_id VARCHAR(8) NOT NULL REFERENCES products (product_id),
    quantity_on_hand INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_supplier ON products (supplier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_product_recorded ON inventory_snapshots (product_id, recorded_at DESC);

INSERT INTO suppliers (supplier_id, name, country, average_delivery_days) VALUES
    ('S001', 'TechDistribution Polska', 'PL', 3),
    ('S002', 'EuroMonitors GmbH', 'DE', 4),
    ('S003', 'Nordic Accessories', 'SE', 5),
    ('S004', 'Storage World', 'CZ', 2),
    ('S005', 'Network Partner', 'PL', 3),
    ('S006', 'Mobile Europe', 'NL', 6),
    ('S007', 'Audio Premium', 'JP', 8)
ON CONFLICT (supplier_id) DO NOTHING;

INSERT INTO products (product_id, name, category, price, supplier_id, reorder_level, initial_stock) VALUES
    ('P001', 'Laptop Lenovo ThinkPad E14', 'electronics', 3899.99, 'S001', 6, 24),
    ('P002', 'Monitor Dell 27', 'electronics', 1299.0, 'S002', 8, 35),
    ('P003', 'Klawiatura Logitech MX Keys', 'accessories', 469.99, 'S003', 12, 60),
    ('P004', 'Mysz Logitech MX Master 3S', 'accessories', 429.0, 'S003', 10, 55),
    ('P005', 'Dysk SSD Samsung 1TB', 'storage', 349.9, 'S004', 15, 80),
    ('P006', 'Router TP-Link AX55', 'network', 329.0, 'S005', 9, 38),
    ('P007', 'Smartfon Samsung Galaxy A55', 'mobile', 1899.0, 'S006', 7, 30),
    ('P008', 'Sluchawki Sony WH-1000XM5', 'audio', 1499.0, 'S007', 5, 22),
    ('P009', 'Tablet Apple iPad Air 11', 'mobile', 2999.0, 'S006', 5, 18),
    ('P010', 'Laptop Dell XPS 13', 'electronics', 6299.0, 'S002', 4, 12),
    ('P011', 'Laptop Apple MacBook Air M3', 'electronics', 5499.0, 'S006', 4, 14),
    ('P012', 'Monitor LG UltraWide 34', 'electronics', 2199.0, 'S002', 5, 20),
    ('P013', 'Monitor Samsung Odyssey G5', 'electronics', 1599.0, 'S002', 6, 26),
    ('P014', 'Stacja dokujaca Dell USB-C', 'accessories', 699.0, 'S001', 8, 32),
    ('P015', 'Hub USB-C Anker 7w1', 'accessories', 249.0, 'S003', 14, 70),
    ('P016', 'Kamera Logitech Brio 4K', 'accessories', 899.0, 'S003', 6, 25),
    ('P017', 'Mikrofon Blue Yeti', 'audio', 599.0, 'S007', 7, 28),
    ('P018', 'Glosnik JBL Charge 5', 'audio', 699.0, 'S007', 8, 36),
    ('P019', 'Sluchawki Apple AirPods Pro 2', 'audio', 1199.0, 'S006', 8, 34),
    ('P020', 'Dysk SSD Crucial 2TB', 'storage', 579.0, 'S004', 10, 48),
    ('P021', 'Dysk zewnetrzny WD Elements 4TB', 'storage', 499.0, 'S004', 10, 45),
    ('P022', 'Pendrive SanDisk Ultra 128GB', 'storage', 69.0, 'S004', 30, 160),
    ('P023', 'Router Asus RT-AX58U', 'network', 549.0, 'S005', 8, 34),
    ('P024', 'Switch TP-Link 8-port Gigabit', 'network', 139.0, 'S005', 15, 75),
    ('P025', 'Access Point Ubiquiti U6 Lite', 'network', 529.0, 'S005', 7, 29),
    ('P026', 'Smartfon Apple iPhone 15', 'mobile', 3999.0, 'S006', 5, 16),
    ('P027', 'Smartfon Xiaomi Redmi Note 13', 'mobile', 999.0, 'S006', 10, 42),
    ('P028', 'Drukarka HP LaserJet M110w', 'office', 549.0, 'S001', 6, 24),
    ('P029', 'Toner HP 142A', 'office', 319.0, 'S001', 14, 65),
    ('P030', 'Fotel biurowy Ergohuman', 'office', 1899.0, 'S001', 3, 11)
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO inventory_snapshots (product_id, quantity_on_hand) VALUES
    ('P001', 24),
    ('P002', 35),
    ('P003', 60),
    ('P004', 55),
    ('P005', 80),
    ('P006', 38),
    ('P007', 30),
    ('P008', 22),
    ('P009', 18),
    ('P010', 12),
    ('P011', 14),
    ('P012', 20),
    ('P013', 26),
    ('P014', 32),
    ('P015', 70),
    ('P016', 25),
    ('P017', 28),
    ('P018', 36),
    ('P019', 34),
    ('P020', 48),
    ('P021', 45),
    ('P022', 160),
    ('P023', 34),
    ('P024', 75),
    ('P025', 29),
    ('P026', 16),
    ('P027', 42),
    ('P028', 24),
    ('P029', 65),
    ('P030', 11)
;
