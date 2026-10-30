"""
Outil interactif pour changer le raccourci clavier de Phoenix Voice.
Détecte automatiquement la touche ou combinaison pressée par l'utilisateur.
"""
import sys
import os
import json
import keyboard

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')

def main():
    print("======================================================")
    print("      ⌨️  MODIFICATION DU RACCOURCI PHOENIX VOICE     ")
    print("======================================================")

    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
        except Exception:
            pass

    current_hotkey = config.get('hotkey', 'ctrl+m')
    print(f"Raccourci actuellement configuré : [{current_hotkey.upper()}]")
    print("\n👉 Appuyez sur la touche ou combinaison souhaitée sur votre clavier...")
    print("   (ex: ctrl+m, f8, f9, alt+space, etc.)")
    print("------------------------------------------------------")

    new_hotkey = keyboard.read_hotkey(suppress=False)

    print(f"\n✨ Touche détectée : [{new_hotkey.upper()}]")
    confirm = input("Voulez-vous enregistrer ce raccourci ? (O/n) : ").strip().lower()

    if confirm in ['', 'o', 'oui', 'y', 'yes']:
        config['hotkey'] = new_hotkey
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Succès ! Le nouveau raccourci est enregistré dans config/config.json : [{new_hotkey.upper()}]")
    else:
        print("\n❌ Modification annulée. L'ancien raccourci est conservé.")

    print("======================================================\n")

if __name__ == '__main__':
    main()
