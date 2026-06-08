from dataclasses import dataclass


@dataclass(frozen=True)
class Config:

    MODEL_DIR: str = "models"
    OUTPUT_PATH: str = "shared-results/prediction_results.json"

    PRODUCTS_PATH: str = "data/products.json"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    SALES_TOPIC: str = "sales"
    DELIVERIES_TOPIC: str = "deliveries"

    KAFKA_WINDOW_SIZE: int = 100

    CI_Z_SCORE: float = 1.96