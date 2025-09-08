import os
import pandas as pd
import json
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
datafile = os.getenv("DATASET_FILE", "OnlineRetail.csv")
input_path = os.path.join("/data/raw", datafile)

print(f"Caricamento dataset {input_path} ...")
df = pd.read_csv(input_path, encoding="unicode_escape")

df.dropna(subset=['Quantity', 'UnitPrice'], inplace=True)


if 'CustomerID' in df.columns:
    df.dropna(subset=['CustomerID'], inplace=True)
    df['CustomerID'] = df['CustomerID'].astype(int)

if 'Quantity' in df.columns:
    df = df[df['Quantity'] >= 0]

if 'Quantity' in df.columns and 'UnitPrice' in df.columns:
    df['TotalPrice'] = df['Quantity'] * df['UnitPrice']

if 'Country' in df.columns:
    countries = sorted(df['Country'].unique())
    country_map = {country: idx for idx, country in enumerate(countries)}
    df['CountryCode'] = df['Country'].map(country_map)
    with open("/data/processed/country_mapping.json", "w") as f:
        json.dump(country_map, f)
    df.drop('Country', axis=1, inplace=True)

if 'StockCode' in df.columns:
    encoder = LabelEncoder()
    df['StockCode'] = encoder.fit_transform(df['StockCode'])
    with open("/data/processed/stockcode_mapping.json", "w") as f:
        mapping = {str(label): int(code) for label, code in zip(encoder.classes_, encoder.transform(encoder.classes_))}
        json.dump(mapping, f)

for col in ['InvoiceNo', 'Description', 'InvoiceDate']:
    if col in df.columns:
        df.drop(col, axis=1, inplace=True)

output_path = "/data/processed/OnlineRetail_cleaned.csv"
df.to_csv(output_path, index=False)
print(f"Dati puliti salvati in {output_path} ({len(df)} record).")
