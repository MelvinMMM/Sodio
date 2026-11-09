"""
Point d'entrée principal de Sodio (Sonic-Audio).
Orchestre le raccourci clavier global non-bloquant avec LIVE AUTO-RELOAD,
la capture audio in-memory warm stream, l'appel à Gemini, le HUD et le System Tray.
"""
import os
import sys
import time
import threading
import subprocess
import keyboard
import sounddevice as sd

if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
LEXIQUE_PATH = os.path.join(BASE_DIR, 'config', 'lexique.json')

sys.path.insert(0, PYTHON_DIR)

from config import load_config
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from injector import inject_text
from history_manager import save_entry
from lexique_manager import load_lexique
from sound_effects import play_feedback_sound
from floating_hud import FloatingHUD
from tray_app import run_tray, stop_tray, set_reload_callback, update_tray_menu

toggle_lock = threading.Lock()
config_lock = threading.Lock()

is_recording = False
recorder = None
transcriber = None
hud = None
config = {}
current_hotkey = None
hotkey_hook = None

def play_beep(beep_type):
    """Joue un retour sonore uniquement si l'option audio_feedback est activée (désactivée par défaut)."""
    if config.get('audio_feedback', False):
        play_feedback_sound(beep_type, enabled=True)

def _process_audio_async(wav_bytes, duration):
    """Effectue la transcription et l'injection sans bloquer le hook Windows."""
    try:
        if hud:
            hud.show_processing()
        print("⏳ [Traitement] Transcription audio en cours...")
        text, latency = transcriber.transcribe(wav_bytes, duration)
        active_model = transcriber.get_active_model_name() if transcriber else config.get('model_name', 'whisper-local')
        if text:
            print(f"✨ Transcrit ({duration:.1f}s audio | {latency:.2f}s calcul) : \"{text}\"")
            inject_text(text)
        else:
            print("⚠️ Aucun texte généré (silence ou inintelligible).")

        if config.get('save_history', True):
            save_entry(
                text=text or "[Transcription vide]",
                duration=duration,
                latency=latency,
                model=active_model,
                is_mock=transcriber.is_mock_mode() if transcriber else False,
                wav_bytes=wav_bytes
            )
    except Exception as e:
        print(f"❌ Erreur lors de la transcription: {e}")
        play_beep('error')
        active_model = transcriber.get_active_model_name() if transcriber else 'local_whisper'
        if config.get('save_history', True):
            save_entry(
                text=f"[Erreur: {str(e)[:40]}]",
                duration=duration,
                latency=0.0,
                model=active_model,
                is_mock=False,
                wav_bytes=wav_bytes
            )
    finally:
        if hud:
            hud.hide()

def on_hotkey_pressed():
    """Déclenché à chaque appui sur le raccourci (ultra-rapide, non-bloquant)."""
    global is_recording, recorder, transcriber, config, hud

    if recorder is None or transcriber is None:
        print("⏳ [Sodio] Initialisation des composants en cours, patientez un instant...")
        return

    if not toggle_lock.acquire(blocking=False):
        return

    try:
        if not is_recording:
            # 1. DÉMARRAGE FAST PATH (< 1 ms)
            try:
                play_beep('start')
                recorder.start()
                is_recording = True
                if hud:
                    hud.show_recording()
                print(f"\n🎙️ [Écoute en cours - {current_hotkey.upper()}] Parlez maintenant...")
            except Exception as e:
                print(f"\n❌ Erreur démarrage micro: {e}")
                play_beep('error')
        else:
            # 2. ARRÊT IMMÉDIAT & DÉPORT DU TRAITEMENT (Zéro lag OS)
            play_beep('stop')
            wav_bytes, duration = recorder.stop()
            is_recording = False

            if duration < 0.4 or not wav_bytes:
                if duration < 0.4:
                    print("⚠️ Audio trop court (< 0.4s), ignoré.")
                if hud:
                    hud.hide()
                return

            if hud:
                hud.show_processing()
            threading.Thread(target=_process_audio_async, args=(wav_bytes, duration), daemon=True).start()

    finally:
        toggle_lock.release()

def reload_configuration(force=False):
    """Recharge dynamiquement la configuration (raccourci, micro, IA, HUD) à chaud."""
    global config, current_hotkey, hotkey_hook, recorder, transcriber, hud

    with config_lock:
        try:
            new_cfg = load_config()
            new_hotkey = new_cfg.get('hotkey', 'f4').strip().lower()
            new_mic = new_cfg.get('microphone_index')
            new_engine = new_cfg.get('engine', 'local_whisper')
            new_local_size = new_cfg.get('local_model_size', 'small')
            new_device = new_cfg.get('device', 'auto')
            new_api_key = new_cfg.get('api_key', '')
            new_model = new_cfg.get('model_name', 'gemini-flash-lite-latest')

            # 1. Raccourci Clavier
            if force or (current_hotkey != new_hotkey):
                old_display = (current_hotkey or 'AUCUN').upper()
                if hotkey_hook is not None:
                    try: keyboard.remove_hotkey(hotkey_hook)
                    except Exception: pass
                    hotkey_hook = None
                try:
                    hotkey_hook = keyboard.add_hotkey(new_hotkey, on_hotkey_pressed)
                    current_hotkey = new_hotkey
                    print(f"🔄 [Live-Reload] Raccourci actif : [{new_hotkey.upper()}] (remplace [{old_display}])")
                    if not force: play_beep('reload')
                except Exception as e: print(f"⚠️ Erreur hook raccourci [{new_hotkey}]: {e}")

            if recorder is not None and (force or recorder.device_index != new_mic):
                recorder.set_device(new_mic)
                print(f"🔄 [Live-Reload] Microphone mis à jour : Index [{new_mic}]")

            # 3. Moteur de transcription IA (Local Whisper ou Gemini)
            engine_changed = (
                force or
                (config.get('engine') != new_engine) or
                (config.get('local_model_size') != new_local_size) or
                (config.get('device') != new_device) or
                (config.get('api_key') != new_api_key) or
                (config.get('model_name') != new_model)
            )
            if engine_changed:
                transcriber = Transcriber(
                    engine=new_engine,
                    local_model_size=new_local_size,
                    device=new_device,
                    api_key=new_api_key,
                    model_name=new_model
                )
                print(f"🔄 [Live-Reload] Moteur IA synchronisé : {transcriber.get_active_model_name()}")

            if hud is not None: hud.enabled = new_cfg.get('floating_hud', True)

            config = new_cfg

            # 5. Rafraîchissement Tray
            try:
                update_tray_menu()
            except Exception:
                pass

        except Exception as e:
            print(f"⚠️ Erreur lors du reload de configuration: {e}")

def start_config_watcher():
    """Thread surveillant les modifications de config.json et lexique.json."""
    def _loop():
        last_cfg = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0
        last_lex = os.path.getmtime(LEXIQUE_PATH) if os.path.exists(LEXIQUE_PATH) else 0

        while True:
            time.sleep(0.5)
            changed = False
            if os.path.exists(CONFIG_PATH):
                m = os.path.getmtime(CONFIG_PATH)
                if m > last_cfg:
                    last_cfg, changed = m, True
            if os.path.exists(LEXIQUE_PATH):
                m = os.path.getmtime(LEXIQUE_PATH)
                if m > last_lex:
                    last_lex, changed = m, True
            if changed:
                reload_configuration(force=False)

    threading.Thread(target=_loop, daemon=True).start()

def main():
    global config, recorder, transcriber, hud

    config = load_config()

    def _init_in_background(icon):
        global config, recorder, transcriber, hud
        try:
            if icon is not None and hasattr(icon, 'visible') and not icon.visible:
                icon.visible = True
            mic_idx = config.get('microphone_index')
            engine = config.get('engine', 'local_whisper')
            local_size = config.get('local_model_size', 'small')
            device = config.get('device', 'auto')
            api_key = config.get('api_key', '')
            model_name = config.get('model_name', 'gemini-flash-lite-latest')

            # Ne proposer la clé API que si le mode Cloud Gemini est actif sans clé
            if engine == 'gemini' and (not api_key or api_key.strip() in ['VOTRE_CLE_GEMINI_AI_STUDIO', '']):
                subprocess.Popen(['pythonw.exe', os.path.join(PYTHON_DIR, 'changer_cle_api.py')], cwd=BASE_DIR, shell=True)

            from history_manager import purge_old_recordings
            try:
                purge_old_recordings(hours=24)
            except Exception:
                pass

            recorder = AudioRecorder(device_index=mic_idx)
            transcriber = Transcriber(
                engine=engine,
                local_model_size=local_size,
                device=device,
                api_key=api_key,
                model_name=model_name
            )
            hud = FloatingHUD(enabled=config.get('floating_hud', True))

            set_reload_callback(lambda: reload_configuration(force=True))
            reload_configuration(force=False)
            start_config_watcher()
            threading.Thread(target=transcriber.warmup, daemon=True).start()

            mic_display = "Défaut Windows"
            try:
                active_idx = mic_idx if mic_idx is not None else sd.default.device[0]
                dev_info = sd.query_devices(active_idx)
                mic_display = f"[{active_idx}] {dev_info.get('name', 'Micro')}" + (" (Auto)" if mic_idx is None else "")
            except Exception:
                mic_display = f"Index [{mic_idx}]" if mic_idx is not None else "Inconnu"

            lex_data = load_lexique()
            mots_cles = lex_data.get('mots_cles_perso', []) or lex_data.get('mots_cles_phoenix', [])
            nb_termes = len(lex_data.get('termes_metier', [])) + len(mots_cles)
            active_engine_label = transcriber.get_active_model_name()
            print("⚡ SODIO (SONIC-AUDIO) — MICRO-AGENT VOCAL DE MELVIN")
            print(f"• Raccourci : [{current_hotkey.upper()}] (Sonic-Toggle ⚡) | Micro : {mic_display}")
            print(f"• Lexique   : {nb_termes} termes | HUD : {'Activé (Aura Sonic) 🟣' if config.get('floating_hud', True) else 'Désactivé'}")
            print(f"• Moteur    : {'⚡ ' + active_engine_label.upper() if not transcriber.is_mock_mode() else '⚠️ SIMULATION'}")
            print(f"👉 Appuyez sur [{current_hotkey.upper()}] dans n'importe quel logiciel pour dicter.\n")

            update_tray_menu()
        except Exception as e:
            print(f"❌ [Main] Erreur initialisation Sodio: {e}")

    try:
        run_tray(setup_callback=_init_in_background)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        if hud:
            hud.hide()
        if recorder:
            recorder.close()
        stop_tray()

if __name__ == '__main__':
    main()
