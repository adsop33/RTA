import numpy as np


class StockoutEngine:

    def compute_days_to_stockout(self, stock, prediction):

        daily = [
            prediction["d1"],
            prediction["d2"],
            prediction["d3"]
        ]

        remaining = stock
        days = 0

        i = 0

        while remaining > 0:

            remaining -= daily[i % 3]
            days += 1

            i += 1

            if days > 365:
                break

        return round(days, 2)

    def is_stockout_risk(self, ci, stock):

        lower = stock

        for i, d in enumerate(["d1", "d2", "d3"]):

            lower -= ci[d][0]

            if lower <= 0:
                return True

        return False