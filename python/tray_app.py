"""
Module System Tray pour Sodio (Sonic-Audio).
Affiche une icône élégante dans la zone de notification Windows (près de l'horloge)
avec support de rechargement à chaud (Live-Reload) du raccourci, du micro et de la clé API.
"""
import os
import sys
import json
import subprocess
import threading
import sounddevice as sd
from PIL import Image
import pystray
from pystray import MenuItem as Item, Menu

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
LEXIQUE_PATH = os.path.join(BASE_DIR, 'config', 'lexique.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'history', 'history.json')
ICON_PATH = os.path.join(BASE_DIR, 'assets', 'icon.png')

_tray_icon = None
_reload_callback = None

def set_reload_callback(cb):
    global _reload_callback
    _reload_callback = cb

def get_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_current_mic_name():
    cfg = get_config()
    mic_idx = cfg.get('microphone_index')
    try:
        active_idx = mic_idx if mic_idx is not None else sd.default.device[0]
        dev_info = sd.query_devices(active_idx)
        name = dev_info.get('name', 'Microphone')
        if len(name) > 26:
            name = name[:23] + '...'
        return f"[{active_idx}] {name}"
    except Exception:
        return "Micro par défaut"

def on_open_dashboard(icon=None, item=None):
    """Ouvre le Tableau de bord complet Sodio."""
    script_path = os.path.join(PYTHON_DIR, 'gui_app.py')
    subprocess.Popen(['pythonw.exe', script_path], cwd=BASE_DIR, shell=True)

def on_change_api_key(icon=None, item=None):
    """Ouvre la boîte de dialogue de configuration de la clé API Gemini."""
    script_path = os.path.join(PYTHON_DIR, 'changer_cle_api.py')
    subprocess.Popen(['pythonw.exe', script_path], cwd=BASE_DIR, shell=True)

def on_add_lexique_word(icon, item):
    """Ouvre une boîte de dialogue Windows native pour ajouter un mot technique."""
    def _prompt():
        try:
            import tkinter as tk
            from tkinter import simpledialog, messagebox

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            word = simpledialog.askstring(
                "Sodio — Lexique Personnel",
                "Entrez le mot ou nom propre à ajouter :",
                parent=root
            )

            if word and word.strip():
                clean_word = word.strip()
                lex_data = {}
                if os.path.exists(LEXIQUE_PATH):
                    try:
                        with open(LEXIQUE_PATH, 'r', encoding='utf-8-sig') as f:
                            lex_data = json.load(f)
                    except Exception:
                        pass

                key = 'mots_cles_perso' if 'mots_cles_perso' in lex_data else 'mots_cles_phoenix'
                mots = lex_data.get(key, [])
                if clean_word not in mots:
                    mots.append(clean_word)
                    lex_data[key] = mots
                    with open(LEXIQUE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(lex_data, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo(
                        "Sodio",
                        f"✅ '{clean_word}' a été ajouté avec succès à votre lexique !"
                    )
                    if _reload_callback:
                        _reload_callback()
                    update_tray_menu()
                else:
                    messagebox.showinfo("Sodio", f"ℹ️ '{clean_word}' est déjà dans le lexique.")
            root.destroy()
        except Exception as e:
            print(f"Erreur ajout lexique: {e}")

    threading.Thread(target=_prompt, daemon=True).start()

def on_reload_config(icon=None, item=None):
    """Déclenche manuellement le rechargement de la configuration."""
    if _reload_callback:
        _reload_callback()
    update_tray_menu()

def on_change_hotkey(icon, item):
    script_path = os.path.join(PYTHON_DIR, 'changer_raccourci.py')
    subprocess.Popen(['cmd.exe', '/c', 'start', 'python', script_path], cwd=BASE_DIR, shell=True)

def on_change_mic(icon, item):
    script_path = os.path.join(PYTHON_DIR, 'changer_micro.py')
    subprocess.Popen(['cmd.exe', '/c', 'start', 'python', script_path], cwd=BASE_DIR, shell=True)

def on_view_history(icon, item):
    if os.path.exists(HISTORY_FILE):
        os.startfile(HISTORY_FILE)
    else:
        os.startfile(os.path.join(BASE_DIR, 'history'))

def on_open_lexique(icon, item):
    if os.path.exists(LEXIQUE_PATH):
        os.startfile(LEXIQUE_PATH)

def on_quit(icon, item):
    global _tray_icon
    if _tray_icon:
        _tray_icon.stop()

def create_tray_menu():
    cfg = get_config()
    hotkey = cfg.get('hotkey', 'f4').upper()
    mic_name = get_current_mic_name()
    api_key = cfg.get('api_key', '').strip()
    has_valid_key = bool(api_key) and (api_key != 'VOTRE_CLE_GEMINI_AI_STUDIO')
    key_status = "🔑 Clé Gemini : Configurée" if has_valid_key else "⚠️ Clé Gemini : Manquante"

    return Menu(
        Item("🎛️ Ouvrir Sodio (Tableau de bord)", on_open_dashboard, default=True),
        Menu.SEPARATOR,
        Item(f"⚡ Sodio : Prêt [{hotkey}]", lambda icon, item: None, enabled=False),
        Item(f"🎙️ Micro : {mic_name}", lambda icon, item: None, enabled=False),
        Item(key_status, lambda icon, item: None, enabled=False),
        Menu.SEPARATOR,
        Item("🔑 Configurer la Clé API Gemini...", on_change_api_key),
        Item("➕ Ajouter un mot au lexique...", on_add_lexique_word),
        Item("⌨️ Changer le raccourci clavier...", on_change_hotkey),
        Item("🎙️ Changer de microphone...", on_change_mic),
        Menu.SEPARATOR,
        Item("🔄 Recharger la configuration", on_reload_config),
        Item("📜 Consulter l'historique des dictées", on_view_history),
        Item("📖 Ouvrir le fichier lexique", on_open_lexique),
        Menu.SEPARATOR,
        Item("❌ Quitter Sodio", on_quit)
    )

def update_tray_menu():
    global _tray_icon
    if _tray_icon:
        try:
            cfg = get_config()
            hotkey = cfg.get('hotkey', 'f4').upper()
            _tray_icon.title = f"Sodio (Sonic-Audio) [{hotkey}]"
            _tray_icon.menu = create_tray_menu()
            _tray_icon.update_menu()
        except Exception as e:
            print(f"⚠️ Erreur update_tray_menu: {e}")

def run_tray():
    """Démarre l'icône sur le thread principal pour alimenter la boucle de messages Windows."""
    global _tray_icon
    try:
        if os.path.exists(ICON_PATH):
            image = Image.open(ICON_PATH).convert('RGBA')
        else:
            image = Image.new('RGBA', (64, 64), color=(157, 78, 221, 255))

        cfg = get_config()
        hotkey = cfg.get('hotkey', 'f4').upper()

        _tray_icon = pystray.Icon(
            "Sodio",
            image,
            f"Sodio (Sonic-Audio) [{hotkey}]",
            menu=create_tray_menu()
        )
        print("Sodio tray icon starting run() loop...")
        _tray_icon.run()
    except Exception as e:
        print(f"⚠️ [Tray] Erreur icône: {e}")

def stop_tray():
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
