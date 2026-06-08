from dataclasses import dataclass


@dataclass(frozen=True)
class Config:

    INPUT_PATH: str = "shared-results/prediction_results.json"

    OUTPUT_DIR: str = "reports"

    CSV_FORECAST_FILE: str = "sales_forecast.csv"
    CSV_RISK_FILE: str = "stockout_risk.csv"

    HTML_FILE: str = "index.html"