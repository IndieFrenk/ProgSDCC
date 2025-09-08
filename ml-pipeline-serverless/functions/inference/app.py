
from flask import Flask, request, jsonify
import joblib
import json
import numpy as np
import pandas as pd
app = Flask(__name__)

model = joblib.load("/data/model/model.pkl")
scaler = joblib.load("/data/model/scaler.pkl")

with open("/data/processed/country_mapping.json", "r") as f:
    country_map = json.load(f)
with open("/data/processed/stockcode_mapping.json", "r") as f:
    stockcode_map = json.load(f)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    try:
        qty = float(data.get("Quantity", 0))
        price = float(data.get("UnitPrice", 0))
        customer_id = int(data.get("CustomerID", -1))
        country = data.get("Country")
        country_code = country_map.get(str(country), 0)
        stockcode = data.get("StockCode")
        if stockcode is not None and str(stockcode) in stockcode_map:
            stockcode_code = stockcode_map[str(stockcode)]
        else:
            stockcode_code = 0
        X_df = pd.DataFrame([{
            "Quantity": qty,
            "UnitPrice": price,
            "CustomerID": customer_id,
            "StockCode": stockcode_code,
            "CountryCode": country_code
        }])
        columns = joblib.load("/data/model/columns.pkl")
        X_df = X_df[columns]

        X_scaled = scaler.transform(X_df)
        prediction = model.predict(X_scaled)
        result = {"predicted_value": prediction[0]}
    except Exception as e:
        result = {"error": str(e)}
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)