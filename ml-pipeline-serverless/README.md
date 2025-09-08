# ML Pipeline Serverless (Docker Local Execution)

Progetto per il corso di **Sistemi Distribuiti e Cloud Computing**, a.a. 2024/2025  
Studente: **Francesco Pelle**  
Matricola: **269857**

---

## 📌 Descrizione

Questo progetto implementa una **pipeline automatizzata per il Machine Learning** basata su **architettura serverless simulata tramite Docker**. Il flusso dati è orchestrato localmente e include:

1. **Caricamento di un dataset Excel** (Online Retail).
2. **Conversione automatica in CSV**.
3. **Pulizia e trasformazione dei dati**.
4. **Addestramento di un modello ML**.
5. **Servizio HTTP REST per inferenza in tempo reale**.

Il sistema è completamente containerizzato e pensato per l'esecuzione locale via Docker Engine.

---

## 🗂️ Struttura del progetto

ml-pipeline-serverless/
├── data/                    # Area di storage condivisa tra container
│   ├── raw/                # File Excel e CSV grezzi
│   ├── processed/          # Dataset pulito + mapping Paesi
│   └── model/              # Modello serializzato (.pkl)
├── functions/
│   ├── converter/          # Funzione: Excel → CSV
│   ├── cleaning/           # Funzione: Data cleaning
│   ├── training/           # Funzione: Model training
│   └── inference/          # Servizio Flask per inferenza
├── orchestrator.py         # Trigger automatico delle fasi
├── gui_launcher.py         # Interfaccia grafica log + test JSON
├── start_pipeline.bat      # Script di avvio Windows
└── README.md               # (questo file)


---

## 🚀 Avvio rapido

### 1. Prerequisiti

- Docker Engine installato
- Python 3.9+ (solo per `orchestrator.py` e `gui_launcher.py`)
- Librerie Python:
  ```bash
  pip install watchdog requests
## 2. Costruzione delle immagini Docker

Aprire un terminale nella cartella principale del progetto e costruire le immagini necessarie:

```bash
docker build -t ml-pipeline-converter ./functions/converter
docker build -t ml-pipeline-cleaning ./functions/cleaning
docker build -t ml-pipeline-training ./functions/training
docker build -t ml-pipeline-inference ./functions/inference
```

## 3. Avvio dell'orchestratore

Eseguire il file Python che monitora la cartella `data/raw/` per l'upload del dataset:

```bash
python orchestrator.py
```

Una volta in esecuzione, copiare un file Excel `OnlineRetail.xlsx` nella cartella:

```bash
data/raw/
```

Questo avvierà automaticamente le seguenti fasi:

- conversione Excel → CSV
- data cleaning
- training del modello con StandardScaler
- salvataggio di: model.pkl, scaler.pkl, columns.pkl
- avvio del servizio di inferenza

## 4. Test dell'inferenza via terminale

Una volta attivo il servizio (di default su `localhost:5000`), si può testare con una richiesta HTTP POST via curl:

```bash
curl -X POST http://localhost:5000/predict \
-H "Content-Type: application/json" \
-d '{"Quantity": 10, "UnitPrice": 2.5, "Country": "France"}'
```