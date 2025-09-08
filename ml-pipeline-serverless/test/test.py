#!/usr/bin/env python3
"""
Test script per verificare il funzionamento dell'API ML Pipeline
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"
INFERENCE_URL = "http://localhost:5000"

def test_connection():
    """Test connessione al server"""
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            print("✅ Server web raggiungibile")
            return True
        else:
            print(f"❌ Server web non risponde correttamente: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al server web. Assicurati che sia in esecuzione su porta 8080")
        return False

def test_upload(file_path):
    """Test upload file"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/upload", files=files)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ File caricato con successo: {data.get('filename')}")
                return True
            else:
                print(f"❌ Errore upload: {data.get('error')}")
                return False
        else:
            print(f"❌ Errore HTTP durante upload: {response.status_code}")
            return False
    except FileNotFoundError:
        print(f"❌ File non trovato: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Errore durante upload: {e}")
        return False

def wait_for_pipeline():
    """Attende il completamento della pipeline"""
    print("⏳ Attendo il completamento della pipeline...")
    max_wait = 120  # 2 minuti massimo
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/status")
            if response.status_code == 200:
                status = response.json()

                # Controlla se tutte le fasi sono complete
                all_complete = all(
                    phase['status'] == 'completed'
                    for phase in status['phases'].values()
                )

                # Controlla se c'è stato un errore
                has_error = any(
                    phase['status'] == 'error'
                    for phase in status['phases'].values()
                )

                if has_error:
                    print("❌ Pipeline fallita con errore")
                    for phase_name, phase_info in status['phases'].items():
                        if phase_info['status'] == 'error':
                            print(f"   Errore in fase {phase_name}: {phase_info.get('message', '')}")
                    return False

                if all_complete:
                    print("✅ Pipeline completata con successo")
                    return True

                # Mostra progresso
                current_phase = status.get('current_phase', 'unknown')
                print(f"   Fase corrente: {current_phase}", end='\r')

            time.sleep(2)
        except Exception as e:
            print(f"❌ Errore durante controllo stato: {e}")
            return False

    print("❌ Timeout: la pipeline non si è completata in tempo")
    return False

def test_dataset_preview():
    """Test visualizzazione dataset"""
    try:
        response = requests.get(f"{BASE_URL}/dataset/preview")
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data:
                print(f"✅ Dataset disponibile: {data['rows']} righe, {data['columns']} colonne")
                print(f"   Sorgente: {data['source']}")
                print(f"   Colonne: {', '.join(data['column_names'][:5])}...")
                return True
            else:
                print(f"❌ Errore lettura dataset: {data['error']}")
                return False
        else:
            print(f"❌ Errore HTTP durante lettura dataset: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore durante lettura dataset: {e}")
        return False

def test_model_info():
    """Test informazioni modello"""
    try:
        response = requests.get(f"{BASE_URL}/model/info")
        if response.status_code == 200:
            data = response.json()
            if data.get('model_exists'):
                print("✅ Modello disponibile")
                if 'features' in data:
                    print(f"   Features: {', '.join(data['features'])}")
                if 'countries' in data:
                    print(f"   Paesi disponibili: {len(data['countries'])}")
                return True
            else:
                print("❌ Modello non ancora disponibile")
                return False
        else:
            print(f"❌ Errore HTTP durante controllo modello: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore durante controllo modello: {e}")
        return False

def test_inference():
    """Test predizione"""
    test_data = {
        "Quantity": 5,
        "UnitPrice": 3.5,
        "CustomerID": 12680,
        "StockCode": "85123A",
        "Country": "France"
    }

    try:
        # Prova prima attraverso il web server
        response = requests.post(
            f"{BASE_URL}/predict",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            if 'predicted_value' in result:
                print(f"✅ Predizione eseguita con successo")
                print(f"   Input: {json.dumps(test_data, indent=2)}")
                print(f"   Output: €{result['predicted_value']:.2f}")
                return True
            elif 'error' in result:
                print(f"❌ Errore durante predizione: {result['error']}")
                return False
        elif response.status_code == 503:
            print("❌ Servizio di inferenza non disponibile")
            return False
        else:
            print(f"❌ Errore HTTP durante predizione: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore durante test inferenza: {e}")
        return False

def test_clear():
    """Test reset pipeline"""
    try:
        response = requests.get(f"{BASE_URL}/clear")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Pipeline resettata con successo")
                return True
            else:
                print(f"❌ Errore reset: {data.get('error')}")
                return False
        else:
            print(f"❌ Errore HTTP durante reset: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore durante reset: {e}")
        return False

def run_all_tests(dataset_path=None):
    """Esegue tutti i test"""
    print("=" * 50)
    print("🧪 ML Pipeline API Test Suite")
    print("=" * 50)

    results = []

    # Test 1: Connessione
    print("\n1. Test connessione server...")
    results.append(test_connection())
    if not results[-1]:
        print("⚠️ Impossibile continuare senza connessione al server")
        return

    # Test 2: Upload (se fornito un dataset)
    if dataset_path:
        print(f"\n2. Test upload file ({dataset_path})...")
        results.append(test_upload(dataset_path))

        if results[-1]:
            # Test 3: Attendi completamento pipeline
            print("\n3. Attendo completamento pipeline...")
            results.append(wait_for_pipeline())
    else:
        print("\n2. Test upload saltato (nessun file specificato)")

    # Test 4: Preview dataset
    print("\n4. Test preview dataset...")
    results.append(test_dataset_preview())

    # Test 5: Info modello
    print("\n5. Test informazioni modello...")
    results.append(test_model_info())

    # Test 6: Inferenza
    print("\n6. Test inferenza...")
    results.append(test_inference())

    # Test 7: Clear
    print("\n7. Test reset pipeline...")
    results.append(test_clear())

    # Riepilogo
    print("\n" + "=" * 50)
    print("📊 RIEPILOGO TEST")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Test superati: {passed}/{total}")

    if passed == total:
        print("🎉 Tutti i test sono passati!")
    else:
        print(f"⚠️ {total - passed} test falliti")

    return passed == total

if __name__ == "__main__":
    # Controlla se è stato fornito un file dataset come argomento
    dataset_path = None
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
        print(f"📁 Userò il dataset: {dataset_path}")
    else:
        print("💡 Tip: Puoi specificare un file dataset come argomento")
        print("   Esempio: python test_api.py OnlineRetail.xlsx")

    # Esegui tutti i test
    success = run_all_tests(dataset_path)

    # Exit code per CI/CD
    sys.exit(0 if success else 1)