# 📧 Email AI Assistant

Un assistant IA qui surveille ta boîte Gmail, analyse les emails entrants et y répond automatiquement — le tout en local, sans envoyer tes données à des serveurs externes.

Construit avec [Ollama](https://ollama.com), [Mistral 7B](https://ollama.com/library/mistral), [Flask](https://flask.palletsprojects.com) et l'[API Gmail](https://developers.google.com/gmail/api).

---

## ✨ Fonctionnalités

- 🔍 **Surveillance automatique** — vérifie les nouveaux emails toutes les X minutes (configurable)
- 🤖 **Classification IA** — distingue les emails simples, complexes et les notifications inutiles
- ⚡ **Réponse automatique** — répond instantanément aux emails simples sans intervention humaine
- 🖥️ **Interface de validation** — propose les réponses complexes à la relecture avant envoi
- 🔔 **Notifications desktop** — alerte quand un email complexe nécessite ton attention
- ⏸️ **Pause / Reprise** — contrôle la surveillance depuis l'interface web
- 📝 **Logs d'activité** — historique complet dans `logs/activity.log`
- 🔒 **100% local** — le modèle IA tourne sur ta machine, aucune donnée envoyée à l'extérieur

---

## 🛠️ Prérequis

- Python 3.10+
- [Ollama](https://ollama.com/download) installé et lancé
- Le modèle Mistral téléchargé
- Un compte Google avec accès à l'API Gmail

---

## 🚀 Installation

**1. Cloner le projet**
```bash
git clone https://github.com/votre-username/email-ai-assistant.git
cd email-ai-assistant
```

**2. Installer les dépendances Python**
```bash
pip install -r requirements.txt
```

**3. Installer Ollama et le modèle**
```bash
# Installer Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle
ollama pull mistral
```

**4. Configurer l'API Gmail**

- Va sur [console.cloud.google.com](https://console.cloud.google.com)
- Crée un projet et active l'**API Gmail**
- Crée des identifiants OAuth2 (Application de bureau)
- Télécharge le fichier JSON et renomme-le `credentials.json`
- Place-le à la racine du projet

**5. Configurer le projet**
```bash
cp .env.example .env
# Modifie .env selon tes besoins
```

**6. Première connexion Gmail**
```bash
python3 connexion.py
# Le navigateur s'ouvre pour autoriser l'accès
```

**7. Lancer l'assistant**
```bash
python3 app.py
```

**8. Ouvrir l'interface**
```
http://localhost:5001
```

---

## ⚙️ Configuration

Toute la configuration se fait dans le fichier `.env` :

| Variable | Valeur par défaut | Description |
|---|---|---|
| `OLLAMA_URL` | `http://127.0.0.1:11434/api/chat` | Adresse du serveur Ollama |
| `MODELE` | `mistral` | Modèle Ollama à utiliser |
| `PORT` | `5001` | Port du serveur Flask |
| `INTERVALLE_MINUTES` | `5` | Fréquence de vérification des emails |

---

## 🔄 Workflow

```
Nouvel email reçu
       ↓
Filtrage rapide (expéditeurs automatiques)
       ↓
Analyse par Mistral
       ↓
    ┌──┴──┐
Simple   Complexe   Ignorer
   ↓         ↓         ↓
Réponse   File      Marqué
  auto   d'attente  comme lu
envoyée  → validation
         humaine
```

---

## 🗂️ Structure du projet

```
email_assistant/
├── app.py              # Serveur Flask + interface web
├── surveillant.py      # Boucle de surveillance automatique
├── analyseur.py        # Analyse des emails par l'IA
├── envoi.py            # Envoi et file d'attente
├── connexion.py        # Authentification Gmail OAuth2
├── main.py             # Traitement manuel (sans interface)
├── prompt.txt          # Instructions pour l'IA (optionnel)
├── .env                # Configuration (non versionné)
├── .env.example        # Modèle de configuration
├── .gitignore          # Fichiers ignorés par Git
├── requirements.txt    # Dépendances Python
├── README.md           # Ce fichier
├── static/
│   └── app.js          # JavaScript de l'interface
└── logs/
    └── activity.log    # Historique des actions
```

---

## Emails gérés

| Type | Exemples | Action |
|---|---|---|
| **Simple** | Demande d'horaires, demande de catalogue, confirmation | Réponse automatique |
| **Complexe** | Réclamation, remboursement, demande personnalisée | Proposition à valider |
| **Ignoré** | Newsletter, pub, notification automatique | Marqué comme lu |

---

## Personnaliser l'IA

Modifie le fichier `analyseur.py` section `EXPEDITEURS_A_IGNORER` pour ajouter des expéditeurs à filtrer automatiquement.

Pour changer le comportement de classification, modifie le prompt dans la fonction `analyser_email()`.

---

## Licence

MIT — libre d'utilisation, de modification et de distribution.
