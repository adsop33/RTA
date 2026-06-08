from datetime import datetime


class HTMLRenderer:

    def render_table(self, df, title: str):

        rows = ""

        for _, row in df.iterrows():

            risk = row.get("risk", False)

            color = "#d4edda" if not risk else "#f8d7da"

            rows += f"""
            <tr style="background-color:{color}">
                <td>{row['product_id']}</td>
                <td>{row.get('product_name', '')}</td>
                <td>{row['stock']}</td>
                <td>{row.get('prediction_D1', '')}</td>
                <td>{row.get('prediction_D2', '')}</td>
                <td>{row.get('prediction_D3', '')}</td>
                <td>{row.get('CI95_LOW', '')}</td>
                <td>{row.get('CI95_HIGH', '')}</td>
                <td>{row.get('days_to_stockout', '')}</td>
            </tr>
            """

        return f"""
        <h2>{title}</h2>
        <table border="1" cellpadding="5">
            <tr>
                <th>Product ID</th>
                <th>Name</th>
                <th>Stock</th>
                <th>D1</th>
                <th>D2</th>
                <th>D3</th>
                <th>CI LOW</th>
                <th>CI HIGH</th>
                <th>Days to Stockout</th>
            </tr>
            {rows}
        </table>
        """

    def render(self, forecast_df, risk_df):

        now = datetime.utcnow().isoformat()

        html = f"""
        <html>
        <head>
            <title>Warehouse Report</title>
        </head>
        <body>
            <h1>Warehouse Forecast Report</h1>
            <p>Generated at: {now}</p>

            {self.render_table(forecast_df, "Forecast Report")}

            <hr>

            {self.render_table(risk_df, "Risk Report")}
        </body>
        </html>
        """

        return html