"""
Module d'historique local et de rétention audio (24 heures) pour Phoenix Voice.
Gère l'enregistrement des fichiers .wav, la purge automatique et la ré-écoute.
"""
import os
import json
import uuid
import winsound
from datetime import datetime, timedelta

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
HISTORY_DIR = os.path.join(BASE_DIR, 'history')
RECORDINGS_DIR = os.path.join(HISTORY_DIR, 'recordings')
HISTORY_FILE = os.path.join(HISTORY_DIR, 'history.json')

def get_recordings_dir():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    return RECORDINGS_DIR

def purge_old_recordings(hours=24):
    """Purge automatiquement les audios et logs datant de plus de 24 heures."""
    cutoff = datetime.now() - timedelta(hours=hours)
    if not os.path.exists(HISTORY_FILE):
        return

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
            history = json.load(f)
        if not isinstance(history, list):
            return

        cleaned_history = []
        for entry in history:
            ts_str = entry.get('timestamp')
            keep = True
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < cutoff:
                        keep = False
                        # Supprimer le fichier audio associé
                        audio_rel = entry.get('audio_file')
                        if audio_rel:
                            audio_abs = os.path.join(BASE_DIR, audio_rel)
                            if os.path.exists(audio_abs):
                                try:
                                    os.remove(audio_abs)
                                except Exception:
                                    pass
                except Exception:
                    pass
            if keep:
                cleaned_history.append(entry)

        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [History] Erreur lors de la purge: {e}")

def save_entry(text, duration=0.0, latency=0.0, model="gemini-flash-lite-latest", is_mock=False, wav_bytes=None):
    """Sauvegarde la dictée avec son flux audio in-memory sur disque (rétention 24h)."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    audio_rel = None

    if wav_bytes:
        try:
            r_dir = get_recordings_dir()
            ts_file = datetime.now().strftime('%Y%m%d_%H%M%S')
            short_id = uuid.uuid4().hex[:4]
            filename = f"rec_{ts_file}_{short_id}.wav"
            abs_audio_path = os.path.join(r_dir, filename)
            with open(abs_audio_path, 'wb') as f:
                f.write(wav_bytes)
            audio_rel = os.path.relpath(abs_audio_path, BASE_DIR).replace('\\', '/')
        except Exception as e:
            print(f"⚠️ [History] Impossible de sauvegarder l'audio: {e}")

    entry = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "latency_seconds": round(latency, 2),
        "model": model,
        "is_mock": is_mock,
        "text": text or "",
        "audio_file": audio_rel
    }

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []

    history.append(entry)

    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [History] Impossible d'enregistrer l'historique: {e}")

    # Nettoyage automatique des dictées expirées (> 24 heures)
    purge_old_recordings(hours=24)
    return entry

def load_history():
    """Charge l'historique complet des dictées récentes."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            pass
    return []

def play_audio(audio_rel_path):
    """Joue un fichier audio .wav de façon asynchrone sans bloquer l'interface."""
    if not audio_rel_path:
        return False
    abs_path = os.path.join(BASE_DIR, audio_rel_path)
    if os.path.exists(abs_path):
        try:
            winsound.PlaySound(abs_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception as e:
            print(f"⚠️ [History] Erreur lecture audio: {e}")
    return False

def stop_audio():
    """Arrête toute lecture audio en cours."""
    try:
        winsound.PlaySound(None, 0)
    except Exception:
        pass

def update_entry_text(entry_id, new_text, new_latency=0.0):
    """Met à jour le texte et la latence après une retranscription manuelle."""
    if not os.path.exists(HISTORY_FILE):
        return False
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
            history = json.load(f)
        for e in history:
            if e.get('id') == entry_id:
                e['text'] = new_text
                e['latency_seconds'] = round(new_latency, 2)
                e['retranscribed_at'] = datetime.now().isoformat()
                break
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
