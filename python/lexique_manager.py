"""
Module de gestion du lexique pour la dictée vocale personnelle de Melvin.
Lit config/lexique.json et injecte le vocabulaire dans le prompt système Gemini.
"""
import os
import json

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PYTHON_DIR)
LEXIQUE_PATH = os.path.join(BASE_DIR, 'config', 'lexique.json')

DEFAULT_SYSTEM_PROMPT = """Tu es le moteur de transcription vocale haute précision personnel de Melvin.
Transcris cet extrait audio en français avec une ponctuation naturelle, rigoureuse et aérée.
RÈGLES CRITIQUES :
1. Corrige les hésitations, répétitions orales involontaires et bégaiements (comme 'euh', 'hein', répétitions).
2. Respecte scrupuleusement la casse et l'orthographe exacte des termes techniques, outils et noms propres listés ci-dessous.
3. RÈGLE ABSOLUE : Tu ne dois retourner STRICTEMENT QUE le texte transcrit final, sans aucun commentaire, sans guillemets, sans politesse ni mise en contexte.
4. Si l'enregistrement ne contient aucune parole intelligible (silence, souffle, bruit de fond, clic), ne retourne rien (chaîne vide). Ne répète JAMAIS la consigne.
5. Priorité acoustique stricte : retranscris fidèlement les sons entendus. N'invente ni ne déduis aucun nom propre ou terme du lexique s'il n'est pas distinctement prononcé dans l'audio."""

def load_lexique():
    if not os.path.exists(LEXIQUE_PATH):
        return {"termes_metier": [], "mots_cles_perso": []}
    try:
        with open(LEXIQUE_PATH, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ [Lexique] Erreur lecture lexique.json: {e}")
        return {"termes_metier": [], "mots_cles_perso": []}

def build_system_instruction():
    data = load_lexique()
    instructions = [DEFAULT_SYSTEM_PROMPT]

    termes = data.get("termes_metier", [])
    if termes:
        instructions.append("\nDICTIONNAIRE PHONÉTIQUE & SUBSTITUTIONS OBLIGATOIRES :")
        for item in termes:
            terme = item.get("terme")
            phonetiques = ", ".join(f"'{p}'" for p in item.get("phonetique", []))
            instructions.append(f"- Écris systématiquement '{terme}' si l'utilisateur prononce phonétiquement l'une de ces variantes : {phonetiques}.")

    mots_cles = data.get("mots_cles_perso", []) or data.get("mots_cles_phoenix", [])
    if mots_cles:
        instructions.append("\nVOCABULAIRE TECHNIQUE & NOMS PROPRES PERSONNELS :")
        instructions.append(", ".join(mots_cles))

    return "\n".join(instructions)
