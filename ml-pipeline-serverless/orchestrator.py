import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath)
        if filepath.endswith(".xlsx"):
            print(f"File Excel rilevato: {filename}. Converto in CSV...")
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{os.getcwd()}/data:/data",
                "ml-pipeline-converter"  
            ], check=True)
            filename = "OnlineRetail.csv" 
    
        if filepath.endswith(".csv"):
                print(f"Nuovo file dataset rilevato: {filename}")
                subprocess.run([
                    "docker", "run", "--rm",
                    "-v", f"{os.getcwd()}/data:/data",           
                    "-e", f"DATASET_FILE={filename}",           
                    "ml-pipeline-cleaning"                       
                ], check=True)
                print("Dataset pulito generato, avvio training ML...")
                subprocess.run([
                    "docker", "run", "--rm",
                    "-v", f"{os.getcwd()}/data:/data",
                    "ml-pipeline-training"                      
                ], check=True)
                print("Modello addestrato e salvato, avvio servizio inferenza...")
                subprocess.run([
                    "docker", "run", "-d", "--name", "ml_inference_service",
                    "-v", f"{os.getcwd()}/data:/data",
                    "-p", "5000:5000",                           
                    "ml-pipeline-inference"                      
                ], check=True)
                print("Servizio di inferenza avviato (in ascolto su porta 5000).")

if __name__ == "__main__":
    path_to_watch = os.path.join(os.getcwd(), "data/raw")
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=False)
    observer.start()
    try:
        print(f"[*] Monitoraggio avviato sulla cartella {path_to_watch}. In attesa di file...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
