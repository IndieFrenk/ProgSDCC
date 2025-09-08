import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import requests
import json

def start_orchestrator(log_widget):
    def run():
        process = subprocess.Popen(
            ["python", "orchestrator.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in process.stdout:
            log_widget.insert(tk.END, line)
            log_widget.see(tk.END)
        process.stdout.close()
        process.wait()

    threading.Thread(target=run, daemon=True).start()

def send_json(json_entry, log_widget):
    try:
        payload = json.loads(json_entry.get("1.0", tk.END).strip())
        response = requests.post("http://localhost:5000/predict", json=payload)
        log_widget.insert(tk.END, "\n[Richiesta]\n" + json.dumps(payload, indent=2))
        log_widget.insert(tk.END, "\n[Risposta]\n" + json.dumps(response.json(), indent=2) + "\n")
        log_widget.see(tk.END)
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante l'invio del JSON:\n{e}")

def create_gui():
    window = tk.Tk()
    window.title("ML Pipeline - Console e Test Inferenza")
    window.geometry("800x600")

    log_label = tk.Label(window, text="Log applicazione:")
    log_label.pack(anchor="w", padx=10, pady=(10, 0))

    log_widget = scrolledtext.ScrolledText(window, wrap=tk.WORD, height=20)
    log_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    json_label = tk.Label(window, text="Invia JSON all'inferenza (fase 4):")
    json_label.pack(anchor="w", padx=10, pady=(10, 0))

    json_entry = scrolledtext.ScrolledText(window, wrap=tk.WORD, height=6)
    json_entry.insert(tk.END, '{"Quantity": 5, "UnitPrice": 3.0, "Country": "France"}')
    json_entry.pack(fill=tk.X, padx=10, pady=5)

    send_button = tk.Button(window, text="Invia JSON", command=lambda: send_json(json_entry, log_widget))
    send_button.pack(pady=(0, 10))

    start_orchestrator(log_widget)
    window.mainloop()

create_gui()
