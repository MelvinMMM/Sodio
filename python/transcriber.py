"""
Module de transcription universel pour Sodio (Sonic-Audio).
Supporte :
1. Moteur Local Whisper (faster-whisper) : Ultra-rapide (< 0.5s), 100% hors-ligne,
   accélération matérielle NVIDIA GeForce RTX 2050 (CUDA) avec repli automatique CPU INT8.
2. Moteur Cloud Google Gemini (REST / Multimodal) : Pour comparaison ou fallback.
"""
import os
import io
import sys
import site
import time
import re
import numpy as np
from scipy.io import wavfile

if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# --- 1. Configuration dynamique des DLL CUDA pour Windows ---
def _setup_nvidia_dll_paths():
    """Injecte les répertoires binaires CUDA (cublas, cudnn) dans le PATH Windows et os.add_dll_directory."""
    if sys.platform != 'win32':
        return
    added = []
    try:
        search_dirs = site.getsitepackages()
        if hasattr(site, 'getusersitepackages'):
            search_dirs.append(site.getusersitepackages())
        for s in search_dirs:
            nv_base = os.path.join(s, 'nvidia')
            if os.path.isdir(nv_base):
                for sub in ['cublas', 'cudnn', 'cuda_nvrtc']:
                    bin_dir = os.path.join(nv_base, sub, 'bin')
                    if os.path.isdir(bin_dir) and bin_dir not in added:
                        try:
                            os.add_dll_directory(bin_dir)
                            added.append(bin_dir)
                        except Exception:
                            pass
        if added:
            cur_path = os.environ.get('PATH', '')
            os.environ['PATH'] = ';'.join(added) + ';' + cur_path
    except Exception as e:
        print(f"⚠️ [Transcriber] Erreur configuration DLL CUDA: {e}")

_setup_nvidia_dll_paths()

# --- 2. Vérification des bibliothèques ---
try:
    from faster_whisper import WhisperModel
    import ctranslate2
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from lexique_manager import load_lexique, build_system_instruction

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview"
]

# Cache singleton pour les modèles locaux (évite de recharger le modèle à chaque dictée)
_LOCAL_WHISPER_CACHE = {}

def get_whisper_initial_prompt():
    """Génère l'amorce contextuelle pour Whisper avec le vocabulaire personnel de Melvin."""
    try:
        data = load_lexique()
        keywords = []
        for item in data.get("termes_metier", []):
            t = item.get("terme")
            if t and t not in keywords:
                keywords.append(t)
        for w in (data.get("mots_cles_perso", []) or data.get("mots_cles_phoenix", [])):
            if w and w not in keywords:
                keywords.append(w)
        base = "Dictée vocale en français avec ponctuation naturelle."
        if keywords:
            return base + " Vocabulaire clé : " + ", ".join(keywords) + "."
        return base
    except Exception:
        return "Dictée vocale en français avec ponctuation naturelle."

def apply_lexique_substitutions(text):
    """Applique les remplacements phonétiques configurés dans lexique.json."""
    if not text:
        return text
    try:
        data = load_lexique()
        res = text
        for item in data.get("termes_metier", []):
            target = item.get("terme")
            for phon in item.get("phonetique", []):
                if phon and phon.lower() in res.lower():
                    pattern = re.compile(re.escape(phon), re.IGNORECASE)
                    res = pattern.sub(target, res)
        return res
    except Exception:
        return text

class Transcriber:
    def __init__(self, engine="local_whisper", local_model_size="small", device="auto",
                 api_key=None, model_name="gemini-flash-lite-latest"):
        self.engine = engine or "local_whisper"
        self.local_model_size = local_model_size or "small"
        self.device_preference = device or "auto"
        self.api_key = (api_key or "").strip()
        self.model_name = model_name or "gemini-flash-lite-latest"

        self.local_model = None
        self.active_device = "cpu"
        self.active_compute_type = "int8"
        self.client = None

        # 1. Initialisation Local Whisper
        if self.engine == "local_whisper" and FASTER_WHISPER_AVAILABLE:
            self._init_local_whisper()
        
        # 2. Initialisation Gemini Client
        if self.engine == "gemini" or (not self.local_model and self.api_key):
            self._init_gemini_client()

    def _init_local_whisper(self):
        global _LOCAL_WHISPER_CACHE
        cache_key = f"{self.local_model_size}_{self.device_preference}"
        if cache_key in _LOCAL_WHISPER_CACHE:
            self.local_model, self.active_device, self.active_compute_type = _LOCAL_WHISPER_CACHE[cache_key]
            return

        chosen_device = self.device_preference
        compute_type = "float16"

        # Détection automatique du GPU NVIDIA RTX avec CUDA
        if chosen_device == "auto":
            try:
                if ctranslate2.get_cuda_device_count() > 0:
                    chosen_device = "cuda"
                    compute_type = "float16"
                else:
                    chosen_device = "cpu"
                    compute_type = "int8"
            except Exception:
                chosen_device = "cpu"
                compute_type = "int8"

        print(f"⚡ [Transcriber] Chargement Whisper '{self.local_model_size}' sur {chosen_device.upper()} ({compute_type})...")
        try:
            self.local_model = WhisperModel(self.local_model_size, device=chosen_device, compute_type=compute_type)
            self.active_device = chosen_device
            self.active_compute_type = compute_type
            print(f"✅ [Transcriber] Whisper '{self.local_model_size}' prêt sur {chosen_device.upper()} !")
        except Exception as e:
            print(f"⚠️ [Transcriber] Échec sur {chosen_device.upper()} ({e}). Bascule de secours sur CPU (INT8)...")
            self.local_model = WhisperModel(self.local_model_size, device="cpu", compute_type="int8", cpu_threads=6)
            self.active_device = "cpu"
            self.active_compute_type = "int8"
            print(f"✅ [Transcriber] Whisper '{self.local_model_size}' secouru sur CPU avec succès !")

        _LOCAL_WHISPER_CACHE[cache_key] = (self.local_model, self.active_device, self.active_compute_type)

    def _init_gemini_client(self):
        if self.api_key and self.api_key not in ["VOTRE_CLE_GEMINI_AI_STUDIO", ""] and GENAI_AVAILABLE:
            try:
                http_opts = types.HttpOptions(
                    timeout=20000,
                    retry_options=types.HttpRetryOptions(attempts=2, initial_delay=0.5, exp_base=1.5)
                )
                self.client = genai.Client(api_key=self.api_key, http_options=http_opts)
            except Exception as e:
                print(f"⚠️ [Transcriber] Erreur initialisation client Gemini: {e}")
                self.client = None

    def is_mock_mode(self):
        if self.engine == "local_whisper":
            return self.local_model is None
        return self.client is None

    def get_active_model_name(self):
        if self.engine == "local_whisper":
            dev = "NVIDIA RTX CUDA" if self.active_device == "cuda" else "CPU INT8"
            return f"Whisper {self.local_model_size} ({dev})"
        return self.model_name

    def warmup(self):
        """Pré-chauffe les cœurs CUDA ou la connexion TCP pour une première dictée instantanée."""
        # 1. Warmup Whisper Local
        if self.local_model is not None:
            try:
                # Synthétise un micro-audio de 0.2s pour chauffer les tenseurs CUDA en RAM
                dummy = np.zeros(16000 // 5, dtype=np.float32)
                list(self.local_model.transcribe(dummy, language="fr", vad_filter=False)[0])
                print("⚡ [Transcriber] Warmup Whisper local terminé (cœurs GPU amorcés) !")
            except Exception as e:
                print(f"⚠️ [Transcriber] Erreur warmup local: {e}")

        # 2. Warmup Gemini Cloud
        if self.client is not None:
            try:
                self.client.models.generate_content(
                    model=self.model_name,
                    contents="ping",
                    config=types.GenerateContentConfig(max_output_tokens=1)
                )
            except Exception:
                pass

    def transcribe(self, wav_bytes, duration):
        start_time = time.time()

        if not wav_bytes:
            return "", 0.0

        # --- BRANCHE A : MOTEUR LOCAL FASTER-WHISPER ---
        if self.engine == "local_whisper" and self.local_model is not None:
            try:
                # Décodage WAV in-memory directement en float32 numpy array (sans PyAV)
                sr, raw_audio = wavfile.read(io.BytesIO(wav_bytes))
                if raw_audio.dtype == np.int16:
                    audio_float = raw_audio.astype(np.float32) / 32768.0
                elif raw_audio.dtype == np.int32:
                    audio_float = raw_audio.astype(np.float32) / 2147483648.0
                elif raw_audio.dtype == np.float32:
                    audio_float = raw_audio
                else:
                    audio_float = raw_audio.astype(np.float32)

                # Si stéréo, convertir en mono
                if len(audio_float.shape) > 1 and audio_float.shape[1] > 1:
                    audio_float = np.mean(audio_float, axis=1)

                # Si l'échantillonnage n'est pas 16kHz, rééchantillonner pour Whisper
                if sr != 16000 and len(audio_float) > 0:
                    from scipy.signal import resample
                    target_length = int(len(audio_float) * 16000 / sr)
                    audio_float = resample(audio_float, target_length).astype(np.float32)

                initial_prompt = get_whisper_initial_prompt()

                segments, info = self.local_model.transcribe(
                    audio_float,
                    language="fr",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=250),
                    initial_prompt=initial_prompt,
                    temperature=0.0,
                    beam_size=5
                )

                collected_segments = []
                for seg in segments:
                    text_seg = seg.text.strip()
                    if text_seg:
                        collected_segments.append(text_seg)

                full_text = " ".join(collected_segments).strip()
                full_text = apply_lexique_substitutions(full_text)

                elapsed = time.time() - start_time
                return full_text, elapsed

            except Exception as e:
                print(f"⚠️ [Transcriber] Erreur Whisper Local: {e}")
                # Si Gemini est disponible, fallback automatique
                if self.client is not None:
                    print("🔄 [Transcriber] Bascule automatique de secours vers Gemini...")
                    return self._transcribe_gemini(wav_bytes, start_time)
                elapsed = time.time() - start_time
                return f"⚠️ [Erreur Whisper] : {e}", elapsed

        # --- BRANCHE B : MOTEUR CLOUD GOOGLE GEMINI ---
        if self.client is not None:
            return self._transcribe_gemini(wav_bytes, start_time)

        # Mode simulation
        elapsed = time.time() - start_time
        simulated = (
            f"[Sodio - Simulation] ⚡ Audio de {duration:.1f}s capturé ! "
            "Le Sonic-Toggle, le presse-papier et le collage automatique fonctionnent."
        )
        return simulated, elapsed

    def _transcribe_gemini(self, wav_bytes, start_time):
        system_instruction = build_system_instruction()
        audio_part = types.Part.from_bytes(
            data=wav_bytes,
            mime_type="audio/wav"
        )
        prompt = (
            "Transcris STRICTEMENT cet enregistrement audio en français avec une ponctuation naturelle.\n"
            "RÈGLE ABSOLUE : Retourne UNIQUEMENT le texte retranscrit, sans guillemets, sans balises, sans aucun commentaire."
        )

        models_to_try = [self.model_name]
        for fb in FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        for current_model in models_to_try:
            try:
                config_params = {
                    "system_instruction": system_instruction,
                    "temperature": 0.0,
                    "max_output_tokens": 1024,
                }
                if any(v in current_model for v in ["3.6", "3.7", "3.8"]):
                    try:
                        config_params["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
                    except Exception:
                        pass

                response = self.client.models.generate_content(
                    model=current_model,
                    contents=[audio_part, prompt],
                    config=types.GenerateContentConfig(**config_params)
                )

                raw_text = response.text or ""
                cleaned = raw_text.strip()
                if cleaned.startswith('"') and cleaned.endswith('"'):
                    cleaned = cleaned[1:-1].strip()

                prompt_echoes = [
                    "transcris fidèlement les paroles de cet enregistrement audio.",
                    "transcris fidèlement les paroles",
                    "transcris cet audio",
                    "transcris cet audio mot à mot.",
                    "transcris strictement cet enregistrement audio en français avec une ponctuation naturelle.",
                    "transcris strictement cet enregistrement audio en français"
                ]
                if cleaned.lower() in prompt_echoes:
                    cleaned = ""

                elapsed = time.time() - start_time
                return cleaned, elapsed

            except Exception as e:
                last_error = str(e)
                print(f"🔄 [Transcriber] Bascule Gemini depuis {current_model} ({last_error[:60]}...)...")
                continue

        elapsed = time.time() - start_time
        print(f"❌ [Transcriber] Échec Gemini: {last_error}")
        return f"⚠️ [Erreur Gemini Cloud] : {last_error}", elapsed
