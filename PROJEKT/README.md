# System zarządzania magazynem

Projekt przedstawia system przetwarzania zdarzeń magazynowych w czasie rzeczywistym z wykorzystaniem Apache Kafka.

System:

* publikuje dane produktów, dostawców i sprzedaży,
* aktualizuje stany magazynowe,
* wykrywa niski stan oraz brak towaru,
* oblicza metryki magazynowe,
* tworzy zlecenia zakupu,
* grupuje produkty według dostawcy,
* publikuje gotowe zamówienia do realizacji.

## Główny przepływ danych

```text
producer
   │
   ├── products
   ├── suppliers
   └── sales
          │
          ▼
      warehouse
          │
          ├── warehouse_states
          ├── warehouse_alerts
          └── warehouse_metrics
                    │
                    ▼
             purchase_orders
                    │
                    ▼
          topic purchase_orders
```

## Używane topiki Kafka

* `products` – dane produktów,
* `suppliers` – dane dostawców,
* `sales` – zdarzenia sprzedaży,
* `warehouse_states` – aktualne stany produktów,
* `warehouse_alerts` – alerty o niskim stanie i braku towaru,
* `warehouse_metrics` – zbiorcze metryki magazynu,
* `purchase_orders` – utworzone zlecenia zakupu.

## Struktura projektu

```text
PROJEKT/
├── data/
├── producer/
├── warehouse/
├── purchase_orders/
├── create_topics.py
└── README.md
```

## Reguła tworzenia zamówienia

Zamówienie powstaje, gdy stan produktu osiągnie próg zamówienia lub spadnie poniżej niego.

Stan docelowy jest obliczany jako:

```text
stan docelowy = 2 × próg zamówienia
```

Ilość zamówienia:

```text
ilość zamówienia = stan docelowy − aktualny stan
```

Produkty są grupowane według dostawcy. Dla każdego dostawcy powstaje jedno zbiorcze zamówienie.

## Uruchomienie projektu

Wszystkie polecenia należy wykonywać z katalogu:

```bash
cd /home/jovyan/notebooks/PROJEKT
```

### 1. Utworzenie topików

```bash
python create_topics.py \
  --bootstrap-servers broker:9092
```

### 2. Moduł zleceń zakupu

Uruchomić w pierwszym terminalu:

```bash
python -m purchase_orders.main \
  --bootstrap-servers broker:9092 \
  --flush-seconds 3 \
  --verbose
```

### 3. Procesor magazynu

Uruchomić w drugim terminalu:

```bash
python -m warehouse.main \
  --bootstrap-servers broker:9092 \
  --metrics-every 10 \
  --verbose
```

### 4. Podgląd utworzonych zamówień

Uruchomić w trzecim terminalu:

```bash
kafka-console-consumer.sh \
  --bootstrap-server broker:9092 \
  --topic purchase_orders \
  --property print.key=true \
  --property key.separator=" | "
```

### 5. Producent danych

Uruchomić jako ostatni, w czwartym terminalu:

```bash
python -m producer.main \
  --bootstrap-servers broker:9092 \
  --scenario demand_spike \
  --events 50 \
  --interval 0.2
```

Aby wyświetlać wszystkie wysyłane zdarzenia, można dodać:

```bash
--print-events
```
### 6. Dashboard

Opcjonalnie: 

Aby utworzyć dashboard na żądanie zawierający dane wsadowe z obecnego momentu, w nowym terminalu:

python -m reporting.generate_report

## Oczekiwany rezultat

Procesor magazynu powinien:

* zmniejszać stan wyłącznie o faktycznie sprzedaną ilość,
* nie pozwalać na ujemny stan magazynowy,
* rejestrować sprzedaż częściową i niezrealizowaną,
* obliczać utracony popyt,
* generować alerty `LOW_STOCK` i `OUT_OF_STOCK`,
* publikować aktualne stany i metryki.

Moduł zleceń zakupu powinien wyświetlić komunikaty podobne do:

```text
UTWORZONO ZAMÓWIENIE ... | dostawca: Mobile Europe (S006) | pozycje: 2 | sztuki: 18
```

W topiku `purchase_orders` powinny pojawić się zamówienia zawierające identyfikator dostawcy oraz listę produktów.

## Kontrola składni

```bash
find . \
  -type f \
  -name "*.py" \
  ! -path "*/.ipynb_checkpoints/*" \
  -print0 \
  | xargs -0 -n1 python -m py_compile
```

Brak komunikatów o błędach oznacza, że wszystkie pliki mają poprawną składnię.

## Założenia minimalnej wersji

* katalog produktów jest publikowany przed rozpoczęciem sprzedaży,
* stan aplikacji jest przechowywany w pamięci podczas działania procesów,
* produkt może mieć tylko jedno aktywne zamówienie podczas jednego uruchomienia modułu,
* realizacja dostaw i zmiany statusów zamówienia znajdują się poza zakresem minimalnej wersji.
