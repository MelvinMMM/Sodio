# Sodio (Sonic-Audio)

<p align="center">
  <img src="assets/sodio_logo.png" alt="Sodio Logo" width="180" style="border-radius: 24px; box-shadow: 0 8px 32px rgba(157, 78, 221, 0.4);" />
  <br>
  <em>Application Windows ultra-rapide de dictée vocale</em>
</p>

---

Application Windows de dictée vocale instantanée conçue pour capturer et retranscrire la parole en texte directement à l'emplacement du curseur dans n'importe quel logiciel.

Propulsée par un double moteur d'intelligence artificielle :
1. **Local Whisper (Par défaut) :** Exécution 100% locale sur la machine (accélération GPU NVIDIA CUDA float16 ou CPU INT8 via `faster-whisper`), garantissant une réponse quasi-instantanée, zéro latence réseau, zéro quota et une confidentialité absolue hors-ligne.
2. **Google Gemini Flash-Lite :** Moteur cloud multimodal connecté pour utilisation distante ou fallback.

* **Auteur :** Melvin Mateta
* **Portfolio :** [https://melvinmateta.netlify.app/](https://melvinmateta.netlify.app/)

---

## Caractéristiques Principales

* **Vitesse Instantanée :** Traitement in-memory ultra-rapide (< 0.3s sur GPU NVIDIA CUDA).
* **100% Souverain & Hors-Ligne :** Aucune dépendance aux serveurs distants en mode local Whisper.
* **Déclenchement Global :** Raccourci clavier universel non-bloquant (`F4` par défaut, personnalisable) sans voler le focus de la fenêtre active.
* **HUD Flottant Discret :** Mini-témoin visuel épuré indiquant l'état d'enregistrement (rouge) et de transcription (jaune).
* **System Tray Windows :** Intégration complète dans la zone de notification avec menu contextuel rapide et accès aux paramètres.
* **Lexique Personnalisé :** Retranscription fidèle du vocabulaire technique, noms propres, acronymes et termes spécifiques avec amorçage Whisper.
* **Tableau de Bord Moderne :** Interface graphique pour configurer les moteurs, régler le micro, tester la vitesse et gérer le vocabulaire.
* **Historique Local (24h) :** Réécoute des dictées, réinjection ou copie en un clic, avec purge automatique quotidienne des fichiers audio temporaires.

---

## Stack Technique

* **Langage & Runtime :** Python 3.10+ (compatible `pythonw.exe` pour exécution silencieuse en arrière-plan).
* **IA Locale :** `faster-whisper` (CTranslate2, CUDA 12, CuDNN, INT8 / FP16).
* **IA Cloud :** Google Gemini Flash-Lite multimodal (`google-genai` / REST API).
* **Audio & Capture :** `sounddevice` (enregistrement in-memory 16 kHz mono), `scipy` / `wave` (traitement direct sans I/O disque superflue).
* **Interface Graphique :** `customtkinter` / `tkinter`, `pystray` / `Pillow` (System Tray Windows).
* **Interactions Windows :** `keyboard` (hook global low-level), `pyperclip` et simulation de frappe pour l'injection directe.

---

## Démarrage Rapide

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Lancement de l'application

* **Lancement discret (recommandé) :** Double-cliquez sur `lancer_silencieux.vbs` ou utilisez le raccourci sur le Bureau.
* **Lancement avec console :** Double-cliquez sur `lancer_sodio.bat` pour visualiser les logs en direct.
* **Arrêt de l'application :** Exécutez `arreter_sodio.bat` ou quittez depuis le menu de l'icône dans la zone de notification.

### 3. Utilisation au quotidien

1. Placez votre curseur dans n'importe quel champ de saisie (navigateur, éditeur de code, traitement de texte, messagerie, etc.).
2. Appuyez sur le raccourci clavier (**F4** par défaut).
3. Dictez naturellement votre texte.
4. Réappuyez sur le raccourci : le texte transcrit et ponctué est injecté directement à la position du curseur.

---

## Structure du Projet

```text
Sodio/
  assets/                  # Identité visuelle (logo, icônes ICO & PNG)
  config/                  # Configuration active et lexique de mots-clés
  history/                 # Journal local et flux audio temporaires (purge 24h)
  python/                  # Moteur applicatif Python
    run.py                 # Lanceur principal avec verrou PID mono-instance
    main.py                # Orchestrateur central et écoute globale
    transcriber.py         # Moteur de transcription (Whisper Local CUDA / Gemini)
    audio_recorder.py      # Capture audio in-memory 16 kHz
    injector.py            # Injection du texte transcrit au curseur
    floating_hud.py        # Mini-badge discret d'état (enregistrement / transcription)
    tray_app.py            # Icône et menu dans la zone de notification Windows
    gui_app.py             # Tableau de bord principal
    gui_tabs.py            # Onglets de configuration (Moteurs IA, Audio, Raccourcis)
    gui_history.py         # Visualiseur et lecteur d'historique des dictées
    history_manager.py     # Gestion de l'historique local et purge automatique
    lexique_manager.py     # Gestion du lexique et des termes personnalisés
    sound_effects.py       # Gestion des retours sonores (optionnel)
  lancer_silencieux.vbs    # Lancement furtif en arrière-plan
  lancer_sodio.bat         # Lancement avec fenêtre de logs
  arreter_sodio.bat        # Arrêt complet et propre de Sodio
```

---

## Sécurité & Confidentialité

* En mode **Local Whisper**, toutes les données audio et transcriptions restent 100% locales sur votre machine. Aucun paquet n'est envoyé sur internet.
* En mode **Cloud Gemini**, les requêtes transitent directement via l'API officielle Google AI Studio avec votre clé privée.
* Les fichiers de configuration sensibles (`config.json`), l'historique et les enregistrements sont exclus du suivi Git via `.gitignore`.
* Les enregistrements audio conservés pour consultation locale sont automatiquement supprimés après 24 heures.
