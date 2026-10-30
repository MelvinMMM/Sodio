# Point Technique : Logique API & Performances — Phoenix Voice

Ce document résume le fonctionnement de la brique de transcription vocale de **Phoenix Voice**, les choix d'optimisation réalisés, ainsi que les pistes d'intégration prévues pour le dashboard de l'entreprise.

---

## 🧠 1. C'est quoi la "Logique API" ?

**En une phrase :** La logique API gère la communication sécurisée entre l'application **Phoenix Voice** et les serveurs de **Google Gemini** pour transformer instantanément la voix en texte.

### Le parcours d'une transcription :
1. **Captation audio :** L'application capture la voix (format optimisé $16\text{ kHz}$ mono, stocké en RAM via `sounddevice`).
2. **Requête HTTPS :** Les octets audio sont envoyés de manière sécurisée à l'API de Google Gemini.
3. **Traitement par le modèle :** Gemini analyse l'audio en s'appuyant sur le modèle par défaut `gemini-3.5-flash`.
4. **Restitution :** Le texte généré est renvoyé à l'application et collé automatiquement (`Ctrl+V`).

---

## 🔑 2. Gestion des Clés API et Quotas

La clé API sert de badge d'authentification auprès des serveurs de Google.

* **Clé API Pro (Agence / Phoenix Performance) :** Utilisée pour la production et les gros volumes de l'équipe.
* **Clé API Personnelle :** Utilisée en secours ou pour les tests individuels (limitée en nombre de requêtes par minute).

Un sélecteur de clé est prévu pour permettre de basculer facilement entre la clé pro et la clé perso selon les besoins opérationnels.

---

## ⚡ 3. Optimisations de Performance

Afin d'obtenir une réactivité maximale (passage d'un temps de réponse global de $\sim 3\text{ s}$ à **moins de $800\text{ ms}$**), plusieurs optimisations clés ont été implémentées dans le code (`transcriber.py` et `config.py`) :

* **Client persistant :** La connexion est instanciée une seule fois au démarrage (évite de recréer une poignée de main HTTPS à chaque phrase).
* **Préchauffe (Warmup) :** La connexion TCP/TLS est initialisée dès le lancement de l'application.
* **Paramètres de génération :** Utilisation de `temperature=0.0` et `thinking_budget=0` pour supprimer le temps de latence de réflexion superflu du modèle.
* **Modèle par défaut :** Paramétrage sur `gemini-3.5-flash` pour garantir la rapidité et la fiabilité des transcriptions.

---

## 🎛️ 4. Prochaines étapes : Intégration Dashboard

Pour offrir une visibilité claire aux utilisateurs et aux administrateurs, l'intégration sur le dashboard de l'entreprise s'articulera autour de deux axes :

1. **Onglet "API & Connexion" :**
   * Statut de connexion en temps réel ($\checkmark$ Connecté / $\times$ Clé invalide).
   * Bouton de test rapide de la clé.
   * Indicateur de quota (Clé Perso vs Clé Pro) et sélecteur de clé.

2. **Onglet "Performance" :**
   * Suivi de la latence de transcription (en millisecondes).
   * Affichage du modèle actif (`gemini-3.5-flash`).
   * Checklist de vérification des optimisations actives.