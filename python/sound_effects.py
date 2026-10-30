"""
Module de retour sonore universel pour Phoenix Voice.
Génère des carillons haute-fidélité en mémoire vive et les joue directement
dans le périphérique audio actif de l'utilisateur (Casque, Écouteurs, MiniFuse, Enceintes)
sans dépendre du buzzer carte mère de Windows.
"""
import threading
import numpy as np
import sounddevice as sd

SR_BEEP = 44100
try:
    sd.default.latency = ('low', 'low')
except Exception:
    pass

def _build_chime(freqs, durations, vol=0.22):
    chunks = []
    for f, d in zip(freqs, durations):
        n = int(SR_BEEP * d)
        t = np.linspace(0, d, n, endpoint=False)
        w = np.sin(2 * np.pi * f * t) * vol
        fade = min(int(SR_BEEP * 0.008), n // 4)
        env = np.ones(n)
        if fade > 0:
            env[:fade] = np.linspace(0, 1, fade)
            env[-fade:] = np.linspace(1, 0, fade)
        chunks.append(w * env)
    return np.concatenate(chunks).astype(np.float32)

# Pré-génération en RAM pour 0ms de latence
BEEP_SOUNDS = {
    'start': _build_chime([784, 1046], [0.05, 0.08], vol=0.25),  # Sol5 -> Do6 (Ascendant)
    'stop': _build_chime([1046, 784], [0.05, 0.07], vol=0.22),   # Do6 -> Sol5 (Descendant)
    'reload': _build_chime([1046, 1318], [0.04, 0.07], vol=0.20),# Double carillon joyeux
    'error': _build_chime([350, 260], [0.09, 0.12], vol=0.28)    # Double tonalité grave
}

def play_feedback_sound(beep_type, enabled=True):
    """Joue le signal sonore demandé de manière asynchrone et instantanée (< 5 ms)."""
    if not enabled:
        return

    def _play():
        # Fast Path Windows Kernel (0 ms de délai, pas de conflit de flux avec le micro)
        try:
            import winsound
            if beep_type == 'start':
                winsound.Beep(1046, 50)  # Do6 aigu (50 ms) -> Démarrage instantané
                return
            elif beep_type == 'stop':
                winsound.Beep(784, 45)   # Sol5 doux (45 ms) -> Fin d'enregistrement
                return
            elif beep_type == 'reload':
                winsound.Beep(1318, 50)  # Mi6 -> Recharge
                return
            elif beep_type == 'error':
                winsound.Beep(350, 100)  # Tonalité grave -> Erreur
                return
        except Exception:
            pass

        # Fallback sounddevice
        sound = BEEP_SOUNDS.get(beep_type)
        if sound is not None:
            try:
                sd.play(sound, samplerate=SR_BEEP)
            except Exception:
                pass

    threading.Thread(target=_play, daemon=True).start()
