"""
Outil interactif pour choisir le microphone utilisé par Phoenix Voice.
Résout les conflits de cartes son sous Windows et permet de verrouiller son micro préféré.
"""
import sys
import os
import json
import sounddevice as sd

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')

def get_input_devices():
    devices = []
    try:
        all_devs = sd.query_devices()
        for idx, dev in enumerate(all_devs):
            if dev.get('max_input_channels', 0) > 0:
                devices.append({
                    'index': idx,
                    'name': dev.get('name', 'Périphérique audio'),
                    'channels': dev.get('max_input_channels', 1)
                })
    except Exception as e:
        print(f"Erreur détection périphériques : {e}")
    return devices

def main():
    print("======================================================")
    print("      🎙️  SÉLECTION DU MICROPHONE - PHOENIX VOICE     ")
    print("======================================================")

    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
        except Exception:
            pass

    current_idx = config.get('microphone_index')

    default_system_idx = None
    try:
        default_system_idx = sd.default.device[0]
    except Exception:
        pass

    devices = get_input_devices()
    if not devices:
        print("❌ Aucun microphone d'entrée détecté sous Windows !")
        input("\nAppuyez sur Entrée pour quitter...")
        return

    print("Voici la liste de vos microphones d'enregistrement disponibles :\n")
    for d in devices:
        idx = d['index']
        name = d['name']
        tags = []
        if current_idx is not None and idx == current_idx:
            tags.append("⭐ SÉLECTIONNÉ ACTUELLEMENT")
        elif current_idx is None and idx == default_system_idx:
            tags.append("👉 PAR DÉFAUT WINDOWS (ACTUELLEMENT ACTIF)")

        tag_str = f"  [{' | '.join(tags)}]" if tags else ""
        print(f"  [{idx}] {name}{tag_str}")

    print("\n------------------------------------------------------")
    print("Entrez le numéro du micro à utiliser (ex: 1, 5, 10).")
    print("Tapez 'auto' ou laissez vide pour utiliser le micro par défaut de Windows.")
    
    choice = input("\n👉 Votre choix : ").strip().lower()

    if choice in ['', 'auto', 'default', 'd']:
        config['microphone_index'] = None
        selected_name = "Par défaut Windows"
        for d in devices:
            if d['index'] == default_system_idx:
                selected_name = f"Par défaut ({d['name']})"
                break
    else:
        try:
            val = int(choice)
            matching = [d for d in devices if d['index'] == val]
            if not matching:
                print(f"❌ Numéro [{val}] introuvable dans la liste ci-dessus.")
                input("\nAppuyez sur Entrée pour quitter...")
                return
            config['microphone_index'] = val
            selected_name = matching[0]['name']
        except ValueError:
            print("❌ Entrée non reconnue. Aucun changement effectué.")
            input("\nAppuyez sur Entrée pour quitter...")
            return

    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Configuration enregistrée avec succès dans config/config.json !")
        print(f"• Micro verrouillé : {selected_name}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

    print("======================================================\n")

if __name__ == '__main__':
    main()
