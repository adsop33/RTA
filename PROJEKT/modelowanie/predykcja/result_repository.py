import json
import os


class ResultRepository:

    def __init__(self, config):
        self.config = config

    def save(self, payload):

        os.makedirs(os.path.dirname(self.config.OUTPUT_PATH), exist_ok=True)

        with open(self.config.OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)