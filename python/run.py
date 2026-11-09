"""
Point d'entrée racine pour Sodio (Sonic-Audio).
Exécuté via: python python/run.py ou les scripts .bat à la racine.
Garantit qu'une seule instance tourne à la fois et gère l'exécution silencieuse sous pythonw.
"""
import sys
import os
import time

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
PID_FILE = os.path.join(BASE_DIR, 'sodio.pid')
LOG_FILE = os.path.join(BASE_DIR, 'sodio.log')

class LogTee:
    encoding = 'utf-8'
    errors = 'replace'

    def __init__(self, filename, original):
        self.file = open(filename, 'a', encoding='utf-8', buffering=1)
        self.original = original

    def write(self, data):
        try:
            self.file.write(data)
            self.file.flush()
        except Exception:
            pass
        if self.original:
            try:
                self.original.write(data)
                self.original.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self.file.flush()
        except Exception:
            pass
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass

    def isatty(self):
        return False

try:
    if sys.stdout is None:
        sys.stdout = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)
    else:
        sys.stdout = LogTee(LOG_FILE, sys.stdout)

    if sys.stderr is None:
        sys.stderr = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)
    else:
        sys.stderr = LogTee(LOG_FILE, sys.stderr)
except Exception:
    pass

def ensure_single_instance():
    cur_pid = os.getpid()
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    old_pid = int(content)
                    if old_pid != cur_pid:
                        os.system(f'taskkill /F /PID {old_pid} >nul 2>&1')
                        time.sleep(0.3)
        except Exception:
            pass

    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(cur_pid))
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
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n❌ [CRASH FATAL SODIO] :\n{err_msg}\n")
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Erreur lors du démarrage de Sodio :\n\n{str(e)[:300]}", "Sodio - Erreur", 0x10)
        except Exception:
            pass
    finally:
        cleanup_pid()
