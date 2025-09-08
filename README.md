# ML Pipeline Serverless - Sistema Distribuito per Analisi Retail

## 📋 Descrizione del Progetto

Questo progetto implementa una pipeline di Machine Learning completamente automatizzata e serverless per l'analisi del dataset OnlineRetail. Il sistema è progettato come un'applicazione distribuita che utilizza Docker containers per orchestrare le diverse fasi del processo di ML, dalla preparazione dei dati all'inferenza.

### 🎯 Obiettivi

- **Automazione Completa**: Pipeline automatica che si attiva al caricamento di nuovi dataset
- **Architettura Serverless**: Utilizzo di container Docker per ogni fase del processo
- **Interfaccia Web Intuitiva**: Dashboard per monitoraggio e interazione con la pipeline
- **Scalabilità**: Architettura modulare facilmente estendibile
- **Real-time Monitoring**: Aggiornamenti in tempo reale dello stato della pipeline

## 🏗️ Architettura del Sistema

### Componenti Principali

1. **Web Interface** (`web_app.py`)
   - Dashboard Flask per il monitoraggio della pipeline
   - Upload e gestione dei dataset
   - Visualizzazione dei risultati e log in tempo reale
   - WebSocket per aggiornamenti real-time

2. **Orchestrator** (`ml-pipeline-serverless/orchestrator.py`)
   - Watchdog per il rilevamento automatico di nuovi file
   - Orchestrazione sequenziale delle fasi della pipeline
   - Gestione degli errori e retry logic

3. **Microservizi Containerizzati**:
   - **Converter**: Conversione Excel → CSV
   - **Cleaning**: Pulizia e preprocessing dei dati
   - **Training**: Addestramento del modello ML
   - **Inference**: Servizio di predizione

### Flusso della Pipeline

```
Dataset Upload → Conversion → Data Cleaning → Model Training → Inference Ready
```

## 🚀 Quick Start

### Prerequisiti

- Docker e Docker Compose installati
- Almeno 4GB di RAM disponibili
- Porte 8080 e 5000 libere

### 1. Clonazione e Avvio

```bash
# Clona il repository
git clone https://github.com/IndieFrenk/ProgSDCC
cd ProgSDCC

# Avvia l'intera pipeline
docker-compose up -d
```

### 2. Accesso all'Interfaccia Web

Apri il browser e vai su: `http://localhost:8080`

### 3. Upload del Dataset

1. Carica un file Excel (.xlsx) o CSV nella sezione upload
2. La pipeline si avvierà automaticamente
3. Monitora il progresso nella dashboard

## 📁 Struttura del Progetto

```
├── docker-compose.yml              # Orchestrazione dei servizi
├── Dockerfile.web                  # Container per l'interfaccia web
├── web_app.py                      # Applicazione Flask principale
├── requirements.txt                # Dipendenze Python
├── templates/
│   └── index.html                  # Template della dashboard
├── data/                           # Directory dati condivisa
│   ├── raw/                        # Dataset originali
│   ├── processed/                  # Dati processati
│   └── model/                      # Modelli ML addestrati
└── ml-pipeline-serverless/
    ├── orchestrator.py             # Orchestratore principale
    ├── gui_launcher.py             # Launcher GUI alternativo
    ├── start_pipeline.bat          # Script di avvio Windows
    └── functions/                  # Microservizi
        ├── converter/              # Conversione formato
        ├── cleaning/               # Pulizia dati
        ├── training/               # Addestramento ML
        └── inference/              # Servizio predizioni
```

## 🔧 Configurazione e Personalizzazione

### Variabili di Ambiente

```yaml
# docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - HOST_DATA_PATH=${PWD}/data
  - MAX_CONTENT_LENGTH=100MB
```

### Modifica dei Parametri ML

I parametri del modello possono essere modificati in:
- `ml-pipeline-serverless/functions/training/train.py`
- `ml-pipeline-serverless/functions/cleaning/cleaning.py`

## 📊 Funzionalità Principali

### Dashboard Web Features

- **Upload Dataset**: Drag & drop o selezione file
- **Monitoraggio Real-time**: Stato delle fasi pipeline
- **Log System**: Log dettagliati di ogni operazione
- **Predizioni**: Interface per test del modello
- **Metriche**: Visualizzazione performance del modello

### API Endpoints

#### Inference Service (Porta 5000)

```bash
# Predizione singola
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Quantity": 5,
    "UnitPrice": 2.50,
    "CustomerID": 12345,
    "Country": "United Kingdom",
    "StockCode": "85123A"
  }'
```

#### Web Service (Porta 8080)

- `GET /` - Dashboard principale
- `POST /upload` - Upload dataset
- `POST /start_pipeline` - Avvio manuale pipeline
- `GET /status` - Stato corrente
- `WebSocket` - Aggiornamenti real-time

## Sviluppo e Testing

### Test Locali

```bash
# Test del servizio di inferenza
cd ml-pipeline-serverless/test
python test.py

# Test manuale della pipeline
cd ml-pipeline-serverless
python orchestrator.py
```

### Logs e Debug

```bash
# Visualizza log dei container
docker-compose logs -f web
docker-compose logs -f inference

# Debug singolo microservizio
docker run --rm -v $(pwd)/data:/data ml-pipeline-cleaning
```



