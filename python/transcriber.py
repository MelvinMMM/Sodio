"""
Module de transcription optimisé pour Sodio (Sonic-Audio).
Vitesse maximale : modèle ultra-rapide gemini-flash-lite-latest
avec plafond de timeout strict, 2 tentatives max et fallback automatique.
"""
import time
from lexique_manager import build_system_instruction

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview"
]

class Transcriber:
    def __init__(self, api_key=None, model_name="gemini-flash-lite-latest"):
        self.api_key = (api_key or "").strip()
        self.model_name = model_name or "gemini-flash-lite-latest"
        self.client = None

        if self.api_key and self.api_key not in ["VOTRE_CLE_GEMINI_AI_STUDIO", ""] and GENAI_AVAILABLE:
            try:
                # Plafond de timeout à 20s et 2 tentatives max pour absorber les légers hoquets Google
                http_opts = types.HttpOptions(
                    timeout=20000,
                    retry_options=types.HttpRetryOptions(attempts=2, initial_delay=0.5, exp_base=1.5)
                )
                self.client = genai.Client(api_key=self.api_key, http_options=http_opts)
            except Exception as e:
                print(f"⚠️ [Transcriber] Erreur initialisation client Gemini: {e}")
                self.client = None

    def is_mock_mode(self):
        return self.client is None

    def warmup(self):
        """Pré-chauffe la connexion TCP/TLS avec Google en arrière-plan."""
        if self.client is None:
            return
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

        if self.client is None:
            simulated_text = (
                f"[Sodio - Simulation] ⚡ Audio de {duration:.1f}s capturé ! "
                "Le Sonic-Toggle, le presse-papier et le collage automatique fonctionnent."
            )
            elapsed = time.time() - start_time
            return simulated_text, elapsed

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
                
                # N'ajouter thinking_budget=0 que pour les modèles avec raisonnement (3.6/3.7/3.8)
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
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith('"') and cleaned_text.endswith('"'):
                    cleaned_text = cleaned_text[1:-1].strip()

                # Éviter toute répétition de consigne
                prompt_echoes = [
                    "transcris fidèlement les paroles de cet enregistrement audio.",
                    "transcris fidèlement les paroles",
                    "transcris cet audio",
                    "transcris cet audio mot à mot",
                    "transcris cet audio mot à mot.",
                    "transcris strictement cet enregistrement audio en français avec une ponctuation naturelle.",
                    "transcris strictement cet enregistrement audio en français",
                    "transcris strictement cet extrait audio en français"
                ]
                if cleaned_text.lower() in prompt_echoes:
                    cleaned_text = ""

                elapsed = time.time() - start_time
                return cleaned_text, elapsed

            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                print(f"🔄 [Transcriber] Bascule rapide depuis {current_model} ({err_msg[:60]}...)...")
                continue

        elapsed = time.time() - start_time
        print(f"❌ [Transcriber] Échec: {last_error}")
        return f"⚠️ [Erreur Phoenix Voice] : {last_error}", elapsed
