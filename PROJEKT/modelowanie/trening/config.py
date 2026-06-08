from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    PRODUCTS_PATH: str = "data/products.json"
    SALES_PATH: str = "data/historical_sales.json"
    DELIVERIES_PATH: str = "data/historical_deliveries.json"

    MODEL_DIR: str = "models"

    DAILY_FREQ: str = "D"

    ROLLING_WINDOWS: tuple = (1, 3, 7, 14, 30)

    KAFKA_WINDOW_SIZE: int = 100

    TRAIN_RATIO: float = 0.8

    RANDOM_STATE: int = 42