from config import Config
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from model_training import ModelTrainer
from evaluation import Evaluator
from model_repository import ModelRepository


def main():

    print("\n[TRAINER] Starting training pipeline...\n")

    config = Config()


    products = DataLoader.load_products(config.PRODUCTS_PATH)
    sales = DataLoader.load_sales(config.SALES_PATH)
    deliveries = DataLoader.load_deliveries(config.DELIVERIES_PATH)


    fe = FeatureEngineer(config)

    print("[TRAINER] Building dataset...")

    dataset = fe.build_dataset(
        products,
        sales,
        deliveries
    )

    print(f"[TRAINER] Dataset size: {len(dataset)}")

    X = dataset[[
        "sales_1d",
        "sales_3d",
        "sales_7d",
        "sales_14d",
        "sales_30d",
        "avg_sales_7d",
        "avg_sales_30d",
        "std_sales_7d",
        "std_sales_30d",
        "trend_7d",
        "price",
        "reorder_level",
        "current_stock",
        "category"
    ]]

    y = dataset[[
        "target_d1",
        "target_d2",
        "target_d3"
    ]]


    split_idx = int(len(dataset) * config.TRAIN_RATIO)

    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]

    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]


    trainer = ModelTrainer(config)
    evaluator = Evaluator()

    results = trainer.train(
        X_train,
        y_train,
        X_test,
        y_test,
        evaluator
    )


    repo = ModelRepository(config)
    repo.save(results, feature_columns=X.columns.tolist())


    print("\n[TRAINER] Training completed\n")

    print(f"Best model: {results['best_model_name']}\n")

    print("Linear evaluation:")
    print(results["linear_eval"])

    print("\nMLP evaluation:")
    print(results["mlp_eval"])

    print("\nBest evaluation:")
    print(results["best_eval"])


if __name__ == "__main__":
    main()