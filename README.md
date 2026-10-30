# Sodio (Sonic-Audio) ? Micro-agent de Dictee Vocale Personnel de Melvin

<p align="center">
  <img src="assets/sodio_logo.png" alt="Sodio Logo" width="180" style="border-radius: 24px; box-shadow: 0 8px 32px rgba(157, 78, 221, 0.4);" />
  <br>
  <em>Inspire de l'energie mystique de Darkspine Sonic (Sonic and the Secret Rings) ? Aura Violette & Anneaux d'Or</em>
</p>

---

Micro-agent Windows souverain et ultra-rapide de dictee vocale, taille sur-mesure pour **Melvin**.

Propulse par l'API multimodale **Google Gemini Flash-Lite**, Sodio capture votre voix directement en memoire vive (RAM) et colle instantanement le texte retranscrit et ponctue dans n'importe quel logiciel en **moins de 1,2 seconde**.

* **Portfolio :** [https://melvinmateta.netlify.app/](https://melvinmateta.netlify.app/)
* **Auteur :** Melvin Mateta

---

## Caracteristiques Principales

* **Vitesse Sonic :** Traitement in-memory ultra-rapide (~1,2 s pour 15s de voix).
* **100% Gratuit :** Fonctionne directement sur le quota personnel gratuit de Google AI Studio.
* **Sonic-Toggle :** Declenchement instantane via raccourci global (par defaut `F4` ou personnalisable) sans voler le focus de votre fenetre active.
* **Aura HUD Flottant :** Mini-badge discret affichant un point dore (enregistrement) et une lueur violette (traitement IA).
* **Lexique Personnel :** Retranscription sans faille de vos termes de code, musique (LMMS, VST, Soundworks), IA et projets personnels.
* **Tableau de Bord Integre :** Interface Dark OLED aux accents Violet Electrique (`#9D4EDD`) et Anneaux d'Or (`#FFD700`).
* **Historique Local (24h) :** Reecoutez vos dictees, relancez une retranscription ou copiez en un clic. Purge automatique quotidienne des flux audio.

---

## Stack Technique

* **Langage & Runtime :** Python 3.10+ (compatible `pythonw.exe` pour execution furtive en arriere-plan).
* **Intelligence Artificielle :** Google Gemini Flash-Lite multimodal (`google-genai` / REST API).
* **Audio & Capture :** `sounddevice` (enregistrement in-memory 16 kHz mono), `scipy` / `wave` (traitement WAV sans ecriture disque initiale).
* **Interface Graphique :** `customtkinter` / `tkinter` (interface Dark OLED moderne), `pystray` / `Pillow` (System Tray Windows).
* **Interactions Windows :** `keyboard` (hook global low-level non-bloquant), `pyperclip` & simulation frappe clavier pour injection directe.

---

## Demarrage Rapide

### 1. Installation des dependances

```bash
pip install -r requirements.txt
```

### 2. Configuration initiale

Au premier lancement, Sodio ouvre automatiquement la fenetre de configuration pour renseigner votre cle d'API Google AI Studio (gratuite). La configuration est sauvegardee localement dans `config/config.json` (ignore par Git).

### 3. Lancement depuis le Bureau ou en arriere-plan

Double-cliquez directement sur le raccourci **Sodio** sur le bureau ou executez :

```bash
lancer_en_arriere_plan.bat
```

Pour fermer l'interface tout en laissant Sodio tourner pres de l'horloge Windows, cliquez sur **"Faire tourner en arriere-plan"**.

### 4. Utilisation au quotidien

1. Placez votre curseur dans n'importe quel champ de saisie (Discord, VS Code, navigateur, Terminal, etc.).
2. Appuyez sur votre raccourci clavier (**F4** par defaut).
3. Dictez naturellement votre texte ou votre code.
4. Reappuyez sur le raccourci : le texte retranscrit et ponctue est automatiquement tape a votre curseur !

---

## Structure du Projet

```text
Sodio/
?
??? assets/                  <-- Identite visuelle Sodio (logo, icones ICO & PNG)
??? config/                  <-- Configuration active (cle API, hotkey) et lexique.json
??? history/                 <-- Journal local et recordings (ignore par Git, purge 24h)
?
??? python/                  <-- Moteur modulaire Python
?   ??? run.py               <-- Lanceur unique securise avec verrou PID
?   ??? main.py              <-- Orchestrateur central, warmup et Sonic-Toggle
?   ??? gui_app.py           <-- Tableau de bord Darkspine Violet & Gold
?   ??? gui_tabs.py          <-- Vues et onglets de configuration
?   ??? gui_history.py       <-- Lecteur et inspecteur d'historique 24h
?   ??? floating_hud.py      <-- Mini-badge lumineux (Or & Violet)
?   ??? transcriber.py       <-- Moteur Gemini Flash-Lite multimodal
?   ??? audio_recorder.py    <-- Capture audio in-memory 16 kHz
?   ??? lexique_manager.py   <-- Gestionnaire de vocabulaire personnel
?
??? lancer_en_arriere_plan.bat  <-- Demarrage silencieux en arriere-plan
??? lancer_sodio.bat            <-- Demarrage avec console de logs
??? arreter_sodio.bat           <-- Arret propre du processus Sodio
```

---

## Securite & Confidentialite

* Aucune donnee audio ou retranscrite n'est envoyee a un serveur tiers autre que l'API officielle Google AI Studio via votre cle privee.
* La cle API et les journaux personnels sont strictement exclus du suivi Git via `.gitignore`.
* Les fichiers audio temporaires conserves pour re-ecoute sont automatiquement purges apres 24 heures.
