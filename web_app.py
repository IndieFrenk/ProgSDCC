from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import subprocess
import threading
import time
import pandas as pd
import json
import requests
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ml-pipeline-secret-key'
app.config['UPLOAD_FOLDER'] = '/app/data/raw'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state for pipeline status
pipeline_status = {
    'current_phase': 'idle',
    'phases': {
        'upload': {'status': 'pending', 'timestamp': None, 'message': ''},
        'conversion': {'status': 'pending', 'timestamp': None, 'message': ''},
        'cleaning': {'status': 'pending', 'timestamp': None, 'message': ''},
        'training': {'status': 'pending', 'timestamp': None, 'message': ''},
        'inference': {'status': 'pending', 'timestamp': None, 'message': ''}
    },
    'model_ready': False,
    'logs': []
}

def emit_status_update():
    """Emit current pipeline status to all connected clients"""
    socketio.emit('status_update', pipeline_status)

def add_log(message, level='info'):
    """Add log message and emit to clients"""
    print(f"[{level.upper()}] {message}")
    log_entry = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message': message,
        'level': level
    }
    pipeline_status['logs'].append(log_entry)
    socketio.emit('new_log', log_entry)

def update_phase(phase, status, message=''):
    """Update phase status and emit to clients"""
    pipeline_status['phases'][phase]['status'] = status
    pipeline_status['phases'][phase]['timestamp'] = datetime.now().strftime('%H:%M:%S')
    pipeline_status['phases'][phase]['message'] = message
    pipeline_status['current_phase'] = phase
    add_log(f"Fase {phase}: {status} - {message}", 'info' if status != 'error' else 'error')
    emit_status_update()

def get_host_data_path():
    """Get the host data path for Docker volume mounting"""
    # Use the HOST_DATA_PATH environment variable if available
    # This is set in docker-compose.yml
    host_path = os.environ.get('HOST_DATA_PATH')
    if host_path:
        return host_path
    # Fallback to a default path
    return "/app/data"

def get_data_path():
    """Get the data directory path inside the container"""
    return "/app/data"

def run_pipeline(filename):
    """Execute the ML pipeline"""
    data_path = get_data_path()
    host_data_path = get_host_data_path()

    try:
        # Phase 1: Conversion (if Excel)
        if filename.endswith('.xlsx'):
            update_phase('conversion', 'running', 'Conversione Excel in CSV...')

            # Check if input file exists
            input_file = os.path.join(data_path, 'raw', filename)
            if not os.path.exists(input_file):
                update_phase('conversion', 'error', f'File {filename} non trovato')
                return

            # Rename file to expected name if needed
            expected_name = "OnlineRetail.xlsx"
            expected_path = os.path.join(data_path, 'raw', expected_name)

            if filename != expected_name:
                add_log(f"Rinomino {filename} in {expected_name}")
                try:
                    # Remove existing file if it exists
                    if os.path.exists(expected_path):
                        os.remove(expected_path)
                    os.rename(input_file, expected_path)
                    filename = expected_name
                except Exception as e:
                    add_log(f"Errore nel rinominare il file: {str(e)}", 'error')
                    update_phase('conversion', 'error', f'Errore nel rinominare il file: {str(e)}')
                    return

            # Execute converter container with host path
            try:
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{host_data_path}:/data",
                    "ml-pipeline-converter"
                ]
                add_log(f"Esecuzione comando: {' '.join(cmd)}")

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    add_log(f"Converter output: {result.stdout}")
                    # Check if CSV was actually created
                    csv_path = os.path.join(data_path, 'raw', 'OnlineRetail.csv')
                    if os.path.exists(csv_path):
                        update_phase('conversion', 'completed', 'File Excel convertito in CSV')
                        filename = "OnlineRetail.csv"
                    else:
                        update_phase('conversion', 'error', 'CSV non creato dopo conversione')
                        return
                else:
                    add_log(f"Converter error: {result.stderr}", 'error')
                    update_phase('conversion', 'error', f"Errore conversione: {result.stderr}")
                    return
            except subprocess.TimeoutExpired:
                update_phase('conversion', 'error', 'Timeout durante la conversione')
                return
            except Exception as e:
                update_phase('conversion', 'error', f'Errore esecuzione converter: {str(e)}')
                return
        else:
            # If it's already a CSV, ensure it has the correct name
            if filename != "OnlineRetail.csv":
                old_path = os.path.join(data_path, 'raw', filename)
                new_path = os.path.join(data_path, 'raw', 'OnlineRetail.csv')
                try:
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(old_path, new_path)
                    filename = "OnlineRetail.csv"
                    add_log(f"Rinominato CSV in {filename}")
                except Exception as e:
                    add_log(f"Errore nel rinominare CSV: {str(e)}", 'error')

        # Phase 2: Cleaning
        update_phase('cleaning', 'running', 'Pulizia e trasformazione dati...')

        # Check if CSV exists
        csv_file = os.path.join(data_path, 'raw', filename)
        if not os.path.exists(csv_file):
            update_phase('cleaning', 'error', f'File CSV {filename} non trovato')
            return

        # Create processed directory if it doesn't exist
        os.makedirs(os.path.join(data_path, 'processed'), exist_ok=True)

        try:
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{host_data_path}:/data",
                "-e", f"DATASET_FILE={filename}",
                "ml-pipeline-cleaning"
            ]
            add_log(f"Esecuzione comando: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                add_log(f"Cleaning output: {result.stdout}")
                # Check if cleaned file was created
                cleaned_path = os.path.join(data_path, 'processed', 'OnlineRetail_cleaned.csv')
                if os.path.exists(cleaned_path):
                    update_phase('cleaning', 'completed', 'Dati puliti e trasformati')
                else:
                    update_phase('cleaning', 'error', 'File pulito non creato')
                    return
            else:
                add_log(f"Cleaning error: {result.stderr}", 'error')
                update_phase('cleaning', 'error', f"Errore pulizia: {result.stderr}")
                return
        except subprocess.TimeoutExpired:
            update_phase('cleaning', 'error', 'Timeout durante la pulizia')
            return
        except Exception as e:
            update_phase('cleaning', 'error', f'Errore esecuzione cleaning: {str(e)}')
            return

        # Phase 3: Training
        update_phase('training', 'running', 'Addestramento modello ML...')

        # Create model directory if it doesn't exist
        os.makedirs(os.path.join(data_path, 'model'), exist_ok=True)

        try:
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{host_data_path}:/data",
                "ml-pipeline-training"
            ]
            add_log(f"Esecuzione comando: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                add_log(f"Training output: {result.stdout}")
                # Check if model was created
                model_path = os.path.join(data_path, 'model', 'model.pkl')
                if os.path.exists(model_path):
                    update_phase('training', 'completed', 'Modello addestrato con successo')
                else:
                    update_phase('training', 'error', 'Modello non creato')
                    return
            else:
                add_log(f"Training error: {result.stderr}", 'error')
                update_phase('training', 'error', f"Errore training: {result.stderr}")
                return
        except subprocess.TimeoutExpired:
            update_phase('training', 'error', 'Timeout durante il training')
            return
        except Exception as e:
            update_phase('training', 'error', f'Errore esecuzione training: {str(e)}')
            return

        # Phase 4: Inference Service
        update_phase('inference', 'running', 'Avvio servizio di inferenza...')

        # Stop existing inference service if running
        subprocess.run(["docker", "stop", "ml_inference_service"], capture_output=True)
        subprocess.run(["docker", "rm", "ml_inference_service"], capture_output=True)

        # Start new inference service
        try:
            # Cerca reti che contengono ml_pipeline_network nel nome
            network_cmd = [
                "docker", "network", "ls", "--format", "{{.Name}}", "--filter", "name=ml_pipeline_network"
                ]
            network_result = subprocess.run(network_cmd, capture_output=True, text=True)
            networks = network_result.stdout.strip().split('\n')
    
            # Prendi la prima rete trovata o usa il valore di default
            if networks and networks[0]:
                network_name = networks[0]
                add_log(f"Trovata rete Docker: {network_name}")
            else:
                network_name = "ml_pipeline_network"  # Nome di default dalla docker-compose
                add_log(f"Nessuna rete trovata, utilizzo default: {network_name}", 'warning')
            
            cmd = [
                "docker", "run", "-d", "--name", "ml_inference_service",
                "--network", network_name,
                "-v", f"{host_data_path}:/data",
                "-p", "5000:5000",
                "ml-pipeline-inference"
            ]
            add_log(f"Esecuzione comando: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                time.sleep(5)  # Wait for service to start
                # Test if service is actually running
                try:
                    test_response = requests.get('http://ml_inference_service:5000/predict', timeout=10)
                    update_phase('inference', 'completed', 'Servizio attivo su porta 5000')
                    pipeline_status['model_ready'] = True
                except requests.exceptions.RequestException:
                    # Service might be starting, check container status
                    check_result = subprocess.run([
                        "docker", "ps", "--filter", "name=ml_inference_service", "--format", "{{.Status}}"
                    ], capture_output=True, text=True)

                    if "Up" in check_result.stdout:
                        update_phase('inference', 'completed', 'Servizio in avvio su porta 5000')
                        pipeline_status['model_ready'] = True
                    else:
                        update_phase('inference', 'error', 'Servizio non si è avviato correttamente')
            else:
                add_log(f"Inference error: {result.stderr}", 'error')
                update_phase('inference', 'error', f"Errore inferenza: {result.stderr}")
        except Exception as e:
            update_phase('inference', 'error', f'Errore avvio inferenza: {str(e)}')

    except Exception as e:
        add_log(f"Errore nella pipeline: {str(e)}", 'error')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file selezionato'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400

    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        # Reset pipeline status
        for phase in pipeline_status['phases']:
            pipeline_status['phases'][phase] = {'status': 'pending', 'timestamp': None, 'message': ''}
        pipeline_status['logs'] = []
        pipeline_status['model_ready'] = False

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Ensure directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Save file
        file.save(filepath)
        update_phase('upload', 'completed', f'File {filename} caricato con successo')

        # Start pipeline in background thread
        thread = threading.Thread(target=run_pipeline, args=(filename,))
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'filename': filename})

    return jsonify({'error': 'Formato file non supportato. Usa .xlsx o .csv'}), 400

@app.route('/dataset/preview')
def dataset_preview():
    try:
        data_path = get_data_path()

        # Try to load cleaned dataset first, then raw CSV
        cleaned_path = os.path.join(data_path, 'processed', 'OnlineRetail_cleaned.csv')
        raw_path = os.path.join(data_path, 'raw', 'OnlineRetail.csv')

        if os.path.exists(cleaned_path):
            df = pd.read_csv(cleaned_path)
            source = 'processed'
        elif os.path.exists(raw_path):
            df = pd.read_csv(raw_path, encoding='unicode_escape')
            source = 'raw'
        else:
            return jsonify({'error': 'Nessun dataset disponibile'}), 404

        # Get basic statistics
        stats = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'source': source,
            'sample_data': df.head(100).to_dict('records'),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'null_counts': df.isnull().sum().to_dict()
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json

        # Forward request to inference service
        try:
            response = requests.post('http://ml_inference_service:5000/predict', json=data, timeout=5)
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            add_log(f"Errore chiamata inferenza: {str(e)}", 'error')
            return jsonify({'error': 'Servizio di inferenza non disponibile'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model/info')
def model_info():
    try:
        data_path = get_data_path()

        info = {
            'model_exists': os.path.exists(os.path.join(data_path, 'model', 'model.pkl')),
            'scaler_exists': os.path.exists(os.path.join(data_path, 'model', 'scaler.pkl')),
            'columns_exists': os.path.exists(os.path.join(data_path, 'model', 'columns.pkl')),
            'country_mapping_exists': os.path.exists(os.path.join(data_path, 'processed', 'country_mapping.json')),
            'stockcode_mapping_exists': os.path.exists(os.path.join(data_path, 'processed', 'stockcode_mapping.json'))
        }

        if info['columns_exists']:
            import joblib
            columns = joblib.load(os.path.join(data_path, 'model', 'columns.pkl'))
            info['features'] = columns

        if info['country_mapping_exists']:
            with open(os.path.join(data_path, 'processed', 'country_mapping.json'), 'r') as f:
                info['countries'] = list(json.load(f).keys())

        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def get_status():
    return jsonify(pipeline_status)

@app.route('/clear')
def clear_data():
    try:
        # Stop inference service
        subprocess.run(["docker", "stop", "ml_inference_service"], capture_output=True)
        subprocess.run(["docker", "rm", "ml_inference_service"], capture_output=True)

        # Clear data directories
        data_path = get_data_path()
        for folder in ['raw', 'processed', 'model']:
            folder_path = os.path.join(data_path, folder)
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)

        # Reset status
        for phase in pipeline_status['phases']:
            pipeline_status['phases'][phase] = {'status': 'pending', 'timestamp': None, 'message': ''}
        pipeline_status['logs'] = []
        pipeline_status['model_ready'] = False
        pipeline_status['current_phase'] = 'idle'

        emit_status_update()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    emit('status_update', pipeline_status)

if __name__ == '__main__':
    # Ensure data directories exist
    data_path = get_data_path()
    for folder in ['raw', 'processed', 'model']:
        os.makedirs(os.path.join(data_path, folder), exist_ok=True)

    # Log environment information
    print("=== Environment Info ===")
    print(f"Container data path: {data_path}")
    print(f"Host data path: {get_host_data_path()}")
    print(f"HOST_DATA_PATH env: {os.environ.get('HOST_DATA_PATH', 'NOT SET')}")
    print("========================")

    print("Starting ML Pipeline Web Interface on http://localhost:8080")
    socketio.run(app, debug=True, port=8080, host='0.0.0.0', allow_unsafe_werkzeug=True)