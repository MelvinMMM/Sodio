"""
Module de configuration pour Phoenix Voice.
Gère le chargement, la validation et l'assistant de configuration dans config/config.json.
"""
import os
import json
import sounddevice as sd

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
EXAMPLE_CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.example.json')

DEFAULT_CONFIG = {
    'api_key': '',
    'model_name': 'gemini-flash-lite-latest',
    'hotkey': 'f4',
    'microphone_index': None,
    'audio_feedback': False,
    'floating_hud': True,
    'save_history': True
}

def get_available_microphones():
    microphones = []
    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                microphones.append({
                    'index': idx,
                    'name': dev.get('name', 'Micro inconnu'),
                    'channels': dev.get('max_input_channels', 1),
                    'default_samplerate': dev.get('default_samplerate', 16000)
                })
    except Exception as e:
        print(f"⚠️ [Config] Erreur détection micros: {e}")
    return microphones

def run_onboarding_wizard():
    print("\n======================================================")
    print("  🎙️ BIENVENUE DANS PHOENIX VOICE - CONFIGURATION INITIALE")
    print("======================================================")
    print("Ce petit assistant va configurer votre micro et votre raccourci.\n")

    micros = get_available_microphones()
    print("Périphériques audio d'enregistrement détectés :")
    for m in micros:
        print(f"  [{m['index']}] {m['name']}")

    selected_mic = None
    while selected_mic is None:
        user_input = input("\n👉 Entrez le numéro de votre micro (ou Entrée pour le micro par défaut Windows) : ").strip()
        if user_input == "":
            selected_mic = None
            break
        try:
            val = int(user_input)
            if any(m['index'] == val for m in micros):
                selected_mic = val
                break
            else:
                print("❌ Numéro invalide. Choisissez parmi la liste ci-dessus.")
        except ValueError:
            print("❌ Veuillez entrer un nombre valide.")

    hotkey_input = input("\n👉 Choisissez votre raccourci clavier (ex: ctrl+m, f8, alt+space) [Défaut: ctrl+m] : ").strip()
    selected_hotkey = hotkey_input if hotkey_input else "ctrl+m"

    api_key_input = input("\n👉 Clé API Gemini (optionnelle pour tester, Entrée pour passer) : ").strip()

    config = {
        "api_key": api_key_input,
        "model_name": "gemini-3.5-flash",
        "hotkey": selected_hotkey,
        "microphone_index": selected_mic,
        "audio_feedback": True,
        "save_history": True
    }

    save_config(config)
    print(f"\n✅ Configuration enregistrée dans {CONFIG_PATH} !")
    print("======================================================\n")
    return config

def load_config():
    if not os.path.exists(CONFIG_PATH):
        if os.path.exists(EXAMPLE_CONFIG_PATH):
            try:
                with open(EXAMPLE_CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                    save_config(config)
                    return config
            except Exception:
                pass
        return run_onboarding_wizard()

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
            user_config = json.load(f)
            merged = {**DEFAULT_CONFIG, **user_config}
            return merged
    except Exception as e:
        print(f"⚠️ [Config] Erreur lecture config.json ({e}), chargement config par défaut.")
        return DEFAULT_CONFIG.copy()

def save_config(config_dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)
