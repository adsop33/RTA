from config import Config
from report_generator import ReportGenerator
from csv_exporter import CSVExporter
from html_renderer import HTMLRenderer


def main():

    config = Config()

    generator = ReportGenerator(config)
    exporter = CSVExporter(config)
    renderer = HTMLRenderer()

    print("[REPORTING] Generating reports...")

    forecast_df, risk_df = generator.generate()


    forecast_path = exporter.save(
        forecast_df,
        config.CSV_FORECAST_FILE
    )

    risk_path = exporter.save(
        risk_df,
        config.CSV_RISK_FILE
    )


    html = renderer.render(forecast_df, risk_df)

    html_path = f"{config.OUTPUT_DIR}/{config.HTML_FILE}"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("[REPORTING] Saved:")
    print(forecast_path)
    print(risk_path)
    print(html_path)


if __name__ == "__main__":
    main()