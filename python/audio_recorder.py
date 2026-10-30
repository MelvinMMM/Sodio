"""
Module d'enregistrement audio ultra-rapide et résilient pour Phoenix Voice.
Architecture Warm Audio Stream : maintient le flux WASAPI ouvert en mémoire vive
sans scan matériel à chaque appui. Zéro latence d'initialisation (Fast Path).
Fallback automatique (Slow Path) uniquement en cas d'erreur matérielle.
"""
import io
import time
import threading
import numpy as np
import sounddevice as sd
from scipy.io import wavfile

class AudioRecorder:
    def __init__(self, device_index=None, samplerate=16000, channels=1):
        self.device_index = device_index
        self.samplerate = samplerate
        self.channels = channels
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.start_time = 0.0
        self.duration = 0.0
        self.actual_samplerate = samplerate
        self._lock = threading.Lock()

        # Initialisation anticipée du flux (Warm Stream au démarrage)
        self._ensure_stream_open()

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback continu en RAM. N'accumule que si is_recording est actif."""
        if self.is_recording:
            with self._lock:
                self.frames.append(indata.copy())

    def _try_open_stream(self, device, samplerate):
        """Ouvre et démarre un flux audio persistant."""
        stream = sd.InputStream(
            samplerate=samplerate,
            channels=self.channels,
            dtype='int16',
            device=device,
            callback=self._audio_callback
        )
        stream.start()
        return stream

    def _ensure_stream_open(self):
        """
        Vérifie si le stream est actif (Fast Path).
        Si fermé ou déconnecté, tente la reconnexion avec fallback (Slow Path).
        """
        if self.stream is not None:
            try:
                if self.stream.active:
                    return True
            except Exception:
                pass
            self._close_stream()

        # SLOW PATH : Uniquement à froid ou en cas de déconnexion
        strategies = []
        if self.device_index is not None:
            try:
                dev_info = sd.query_devices(self.device_index)
                native_sr = int(dev_info.get('default_samplerate', 16000))
                strategies.append((self.device_index, self.samplerate))
                if native_sr != self.samplerate:
                    strategies.append((self.device_index, native_sr))
            except Exception:
                strategies.append((self.device_index, self.samplerate))

        strategies.append((None, self.samplerate))
        strategies.append((None, 44100))
        strategies.append((None, 48000))

        try:
            for idx, d in enumerate(sd.query_devices()):
                if d.get('max_input_channels', 0) > 0 and idx != self.device_index:
                    strategies.append((idx, int(d.get('default_samplerate', 44100))))
        except Exception:
            pass

        for dev, sr in strategies:
            try:
                self.stream = self._try_open_stream(dev, sr)
                self.actual_samplerate = sr
                return True
            except Exception:
                continue

        return False

    def _close_stream(self):
        """Ferme proprement le flux audio sans bloquer."""
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def start(self):
        """
        Démarre l'enregistrement audio.
        Fast Path : Si le stream est déjà chaud, activation instantanée en RAM (0 ms).
        Slow Path : Tente de réouvrir si débranché.
        """
        if not self._ensure_stream_open():
            raise RuntimeError("Impossible d'initialiser le microphone.")

        with self._lock:
            self.frames = []
            self.is_recording = True
            self.start_time = time.time()

    def stop(self, min_rms=180.0):
        """
        Arrête l'accumulation et convertit en WAV en RAM.
        Filtre automatiquement le silence pur (clic accidentel ou touche relâchée trop vite).
        Le flux matériel reste ouvert pour la prochaine dictée (Warm Stream).
        """
        with self._lock:
            self.is_recording = False
            self.duration = time.time() - self.start_time
            if not self.frames:
                return None, 0.0
            audio_data = np.concatenate(self.frames, axis=0)
            self.frames = []

        # Détection de silence pour éviter les fausses transcriptions sur appui accidentel
        rms = float(np.sqrt(np.mean(np.square(audio_data.astype(np.float32)))))
        if rms < min_rms:
            print(f"🔇 [Audio] Silence ou clic détecté (RMS {rms:.1f} < {min_rms}), aucun mot prononcé.")
            return None, self.duration

        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, self.actual_samplerate, audio_data)
        return wav_buffer.getvalue(), self.duration

    def set_device(self, new_device_index):
        """Bascule de micro à chaud : ferme l'ancien et préchauffe le nouveau."""
        if self.device_index != new_device_index:
            self.device_index = new_device_index
            self._close_stream()
            self._ensure_stream_open()

    def close(self):
        """Arrêt définitif lors de la fermeture de l'application."""
        self.is_recording = False
        self._close_stream()
