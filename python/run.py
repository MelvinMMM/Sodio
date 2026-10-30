"""
Point d'entrée racine pour Sodio (Sonic-Audio).
Exécuté via: python python/run.py ou les scripts .bat à la racine.
Garantit qu'une seule instance tourne à la fois et gère l'exécution silencieuse sous pythonw.
"""
import sys
import os

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
PID_FILE = os.path.join(BASE_DIR, 'sodio.pid')
LOG_FILE = os.path.join(BASE_DIR, 'sodio.log')

# Redirection sous pythonw (arrière-plan sans console)
if sys.stdout is None or sys.stderr is None:
    try:
        f_log = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)
        if sys.stdout is None:
            sys.stdout = f_log
        if sys.stderr is None:
            sys.stderr = f_log
    except Exception:
        pass

def ensure_single_instance():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    old_pid = int(content)
                    if old_pid != os.getpid():
                        os.system(f'taskkill /F /PID {old_pid} >nul 2>&1')
        except Exception:
            pass

    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

def cleanup_pid():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass

# Ajouter le dossier python au PATH pour les imports directs
sys.path.insert(0, PYTHON_DIR)
from main import main

if __name__ == '__main__':
    ensure_single_instance()
    try:
        main()
    finally:
        cleanup_pid()
