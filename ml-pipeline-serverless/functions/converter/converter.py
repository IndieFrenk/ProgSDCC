
import pandas as pd
import os


input_excel = "/data/raw/OnlineRetail.xlsx"
output_csv = "/data/raw/OnlineRetail.csv"

print(f"Lettura file Excel da: {input_excel}")

try:
    df = pd.read_excel(input_excel)
    print(f"Excel caricato: {len(df)} righe.")
except Exception as e:
    print(f"Impossibile leggere il file Excel: {e}")
    exit(1)
try:
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"File CSV salvato in: {output_csv}")
except Exception as e:
    print(f"Impossibile salvare il file CSV: {e}")
    exit(1)
