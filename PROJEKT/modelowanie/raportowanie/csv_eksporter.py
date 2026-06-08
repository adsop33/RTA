import os
import pandas as pd


class CSVExporter:

    def __init__(self, config):
        self.config = config



    def save(self, df: pd.DataFrame, filename: str):

        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)

        path = os.path.join(self.config.OUTPUT_DIR, filename)

        df.to_csv(path, index=False)

        return path