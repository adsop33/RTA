import json
import os
from datetime import datetime
from kafka import KafkaConsumer, TopicPartition

BOOTSTRAP_SERVERS = "broker:9092"
OUTPUT_FILE = "raport_magazynowy.html"

def main():
    print(f"[{datetime.now().strftime('%T')}] Tworze raport...")
    
    metrics = {}
    alerts = []
    stock_states = {}
    purchase_orders = []

    topics = ["warehouse_metrics", "warehouse_alerts", "warehouse_states", "purchase_orders"]
    
    consumer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP_SERVERS.split(","),
        group_id=None,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))
    )
    
    tp_list = []
    for t in topics:
        partitions = consumer.partitions_for_topic(t)
        if partitions:
            for p in partitions:
                tp_list.append(TopicPartition(t, p))
                
    if not tp_list:
        print("Błąd, topic nieznaleziony")
        consumer.close()
        return

    end_offsets = consumer.end_offsets(tp_list)
    
    consumer.assign(tp_list)
    for tp in tp_list:
        consumer.seek_to_beginning(tp)
        
    finished = {tp: (end_offsets[tp] == 0) for tp in tp_list}
    
    print("Pobieranie danych...")
    
    while not all(finished.values()):
        msg_pack = consumer.poll(timeout_ms=500)
        if not msg_pack:
            break
            
        for tp, messages in msg_pack.items():
            for message in messages:
                if message.offset >= end_offsets[tp]:
                    finished[tp] = True
                    continue
                    
                topic = message.topic
                val = message.value
                
                if topic == "warehouse_metrics":
                    metrics = val
                elif topic == "warehouse_alerts":
                    alerts.insert(0, val)
                elif topic == "warehouse_states":
                    p_id = val.get("product_id")
                    if p_id: stock_states[p_id] = val
                    #print(f"DEBUG kluczy dla produktu {p_id}: {list(val.keys())}")
                elif topic == "purchase_orders":
                    purchase_orders.insert(0, val)
                    
                if message.offset == end_offsets[tp] - 1:
                    finished[tp] = True

    consumer.close()
    print(f"-> Pomyślnie zamrożono stan: {len(stock_states)} produktów w pamięci.")

    table_rows = ""
    if stock_states:
        for p in stock_states.values():
            is_out = p.get("current_stock", 0) <= 0
            is_low = p.get("current_stock", 0) <= p.get("reorder_level", 0)
            row_class = "row-out" if is_out else ("row-low" if is_low else "")
            status_text = "BRAK" if is_out else ("NISKI" if is_low else "OK")

            table_rows += f"""
            <tr class="{row_class}">
                <td>{p.get('product_id')}</td>
                <td><strong>{p.get('product_name')}</strong></td>
                <td>{p.get('category')}</td>
                <td class="text-right font-mono">{p.get('current_stock')}</td>
                <td class="text-right font-mono">{p.get('reorder_level')}</td>
                <td class="text-right font-mono">{p.get('total_sold')}</td>
                <td class="text-center"><span class="badge badge-{status_text.lower()}">{status_text}</span></td>
            </tr>
            """
    else:
        table_rows = "<tr><td colspan='7' class='text-center'>Brak danych w systemie.</td></tr>"

    alerts_html = ""
    if alerts:
        for a in alerts[:10]:
            color = "alert-danger" if a.get("alert_type") == "OUT_OF_STOCK" else "alert-warning"
            alerts_html += f"""<div class="alert {color}"><strong>[{a.get('alert_type')}]</strong> {a.get('product_name')} (Stan: {a.get('current_stock')} szt.)</div>"""
    else:
        alerts_html = "<div class='alert alert-success'>✅ Brak aktywnych alertów.</div>"

    orders_html = ""
    if purchase_orders:
        for po in purchase_orders[:10]:
            orders_html += f"""<div class="order-card"><div class="order-header">Dostawca: {po.get('supplier_id')}</div><div class="order-body text-muted">Pozycji: {len(po.get('items', []))}</div></div>"""
    else:
        orders_html = "<p class='text-muted italic'>Brak wygenerowanych zamówień.</p>"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>Raport Magazynu (Snapshot)</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1300px; margin: 0 auto; }}
            header {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
            h1 {{ margin: 0; font-size: 24px; }}
            .kpi-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 20px; }}
            .kpi-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #3b82f6; }}
            .kpi-title {{ font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; margin: 0 0 5px 0; }}
            .kpi-value {{ font-size: 22px; font-weight: 700; margin: 0; }}
            .main-layout {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
            th {{ background: #f8fafc; padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0; }}
            td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
            .text-right {{ text-align: right; }} .text-center {{ text-align: center; }}
            .font-mono {{ font-family: monospace; font-size: 14px; }}
            .row-low {{ background-color: #fffbeb; }} .row-out {{ background-color: #fef2f2; }}
            .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
            .badge-ok {{ background: #dcfce7; color: #15803d; }} .badge-niski {{ background: #fef3c7; color: #b45309; }} .badge-brak {{ background: #fee2e2; color: #b91c1c; }}
            .alert {{ padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 13px; }}
            .alert-danger {{ background: #fef2f2; color: #991b1b; border: 1px solid #fca5a5; }} .alert-warning {{ background: #fffbeb; color: #92400e; border: 1px solid #fcd34d; }}
            .order-card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; margin-bottom: 8px; }}
            .order-header {{ font-weight: bold; color: #1e3a8a; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>📊 Statystyki i Stan Magazynu</h1>
                    <p style="margin:5px 0 0 0; color:#64748b; font-size:13px;">Raport wygenerowany na żądanie</p>
                </div>
                <div style="text-align: right; font-size: 12px; color: #64748b;">
                    Czas pobrania danych:<br>
                    <strong style="font-size: 14px; color: #334155;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong>
                </div>
            </header>

            <div class="kpi-container">
                <div class="kpi-card" style="border-left-color: #22c55e;"><p class="kpi-title">Przychód Łączny</p><p class="kpi-value">{metrics.get('total_revenue', 0.0):,.2f} PLN</p></div>
                <div class="kpi-card" style="border-left-color: #3b82f6;"><p class="kpi-title">Sprzedany Wolumen</p><p class="kpi-value">{metrics.get('total_units_sold', 0)} szt.</p></div>
                <div class="kpi-card" style="border-left-color: #6366f1;"><p class="kpi-title">Wycena Magazynu</p><p class="kpi-value">{metrics.get('total_stock_value', 0.0):,.2f} PLN</p></div>
                <div class="kpi-card" style="border-left-color: #ef4444;"><p class="kpi-title">Niski stan / Brak produktu</p><p class="kpi-value">{metrics.get('products_low_stock', 0)} / {metrics.get('products_out_of_stock', 0)}</p></div>
            </div>

            <div class="main-layout">
                <div class="card">
                    <h2>📋 Stan Magazynowy i Sprzedaż</h2>
                    <table>
                        <thead>
                            <tr><th>ID Produktu</th><th>Nazwa produktu</th><th>Kategoria</th><th class="text-right">Stan</th><th class="text-right">Próg</th><th class="text-right">Sprzedane</th><th class="text-center">Status</th></tr>
                        </thead>
                        <tbody>{table_rows}</tbody>
                    </table>
                </div>
                <div>
                    <div class="card"><h2>⚠️ Alerty krytyczne</h2>{alerts_html}</div>
                    <div class="card"><h2>📦 Zlecenia Zakupu</h2>{orders_html}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ [{datetime.now().strftime('%T')}] Sukces! Raport zaktualizowany w: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
