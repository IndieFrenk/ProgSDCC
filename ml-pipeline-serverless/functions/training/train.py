import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

data_path = "/data/processed/OnlineRetail_cleaned.csv"
print(f"Caricamento dataset pulito da {data_path} ...")

df = pd.read_csv(data_path)

if 'TotalPrice' not in df.columns:
    raise ValueError("La colonna 'TotalPrice' non è presente nel dataset.")

y = df['TotalPrice']
X = df.drop('TotalPrice', axis=1)
joblib.dump(list(X.columns), "/data/model/columns.pkl")
print(f"Feature utilizzate: {list(X.columns)}")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = LinearRegression()
model.fit(X_scaled, y)

os.makedirs("/data/model", exist_ok=True)
model_path = "/data/model/model.pkl"
joblib.dump(model, "/data/model/model.pkl")
joblib.dump(scaler, "/data/model/scaler.pkl")

print(f"Modello addestrato salvato in {model_path}.")
print(f"Coefficienti del modello: {getattr(model, 'coef_', None)}")

