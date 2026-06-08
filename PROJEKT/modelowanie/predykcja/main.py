import pandas as pd

from config import Config
from kafka_consumer import KafkaEventConsumer
from inventory_manager import InventoryManager
from feature_engineering import FeatureEngineer
from prediction_engine import PredictionEngine
from confidence_interval import ConfidenceInterval
from stockout_engine import StockoutEngine
from result_repository import ResultRepository


def main():

    config = Config()

    products_df = pd.read_json(config.PRODUCTS_PATH)

    inventory = InventoryManager(products_df)
    feature_engine = FeatureEngineer(config)
    predictor = PredictionEngine(config)
    ci_engine = ConfidenceInterval(config)
    stock_engine = StockoutEngine()
    repo = ResultRepository(config)

    history = []

    consumer = KafkaEventConsumer(config)

    print("[PREDICTOR] listening to Kafka...")

    for topic, event in consumer.listen():

        history.append(event)

        history = history[-config.KAFKA_WINDOW_SIZE:]

        product_id = event["product_id"]

        if topic == "sales":
            inventory.apply_sale(product_id, event["quantity"])

        elif topic == "deliveries":
            inventory.apply_delivery(product_id, event["quantity"])

        product_meta = products_df[
            products_df["product_id"] == product_id
        ].iloc[0]

        features = feature_engine.build_features(
            pd.DataFrame(history),
            product_id,
            inventory.get_stock(product_id),
            product_meta
        )

        prediction = predictor.predict(features)
        ci = ci_engine.compute(prediction)

        stockout_days = stock_engine.compute_days_to_stockout(
            inventory.get_stock(product_id),
            prediction
        )

        risk = stock_engine.is_stockout_risk(ci, inventory.get_stock(product_id))

        payload = {
            "product_id": product_id,
            "prediction": prediction,
            "confidence_interval": ci,
            "stock": inventory.get_stock(product_id),
            "days_to_stockout": stockout_days,
            "risk": risk
        }

        repo.save(payload)

        print(f"[UPDATED] {product_id} | risk={risk}")


if __name__ == "__main__":
    main()