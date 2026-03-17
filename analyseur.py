import base64
import re
import json
import requests
from connexion import connecter_gmail

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODELE = "mistral"

# ─────────────────────────────────────────────
# FILTRAGE RAPIDE AVANT L'IA
# On détecte les emails automatiques via
# l'expéditeur AVANT d'appeler Mistral.
# Ça évite de gaspiller du temps sur des
# newsletters ou notifications inutiles.
# ─────────────────────────────────────────────

EXPEDITEURS_A_IGNORER = [
    "no-reply", "noreply", "no_reply",
    "newsletter", "informational",
    "notification", "notifications",
    "donotreply", "do-not-reply",
    "mailer", "automailer",
    "bounce", "hello@", "bonjour@",
    "promo", "marketing", "offre",
    "spartoo", "snapchat", "instagram",
]

def est_email_automatique(expediteur):
    expediteur_lower = expediteur.lower()
    return any(motif in expediteur_lower for motif in EXPEDITEURS_A_IGNORER)


# ─────────────────────────────────────────────
# EXTRACTION DU CONTENU D'UN EMAIL
# ─────────────────────────────────────────────
def extraire_contenu(message):
    headers = message["payload"]["headers"]
    sujet = next((h["value"] for h in headers if h["name"] == "Subject"), "Sans sujet")
    expediteur = next((h["value"] for h in headers if h["name"] == "From"), "Inconnu")

    corps = ""
    payload = message["payload"]

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    corps = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
    elif "body" in payload:
        data = payload["body"].get("data", "")
        if data:
            corps = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    corps = re.sub(r'\n{3,}', '\n\n', corps.strip())

    return {
        "sujet": sujet,
        "expediteur": expediteur,
        "corps": corps[:500]
    }


# ─────────────────────────────────────────────
# ANALYSE PAR L'IA
# Trois classifications possibles :
# - simple   : réponse automatique
# - complexe : réponse à valider par humain
# - ignorer  : newsletter, pub, notif auto
# ─────────────────────────────────────────────
def analyser_email(email):
    prompt = f"""Tu es un assistant de gestion d'emails professionnel. Analyse cet email et réponds UNIQUEMENT en JSON valide, sans texte autour.

Email reçu :
- Expéditeur : {email['expediteur']}
- Sujet : {email['sujet']}
- Corps : {email['corps']}

Réponds avec ce format JSON exact :
{{
  "classification": "simple" ou "complexe" ou "ignorer",
  "raison": "une phrase expliquant la classification",
  "resume": "résumé du besoin en une phrase (vide si ignorer)",
  "reponse_proposee": "la réponse complète à envoyer (vide si ignorer)",
  "langue": "fr" ou "en"
}}

Règles de classification :
- SIMPLE : question fréquente, demande d'info générale, confirmation, accusé de réception
- COMPLEXE : réclamation, problème technique, demande personnalisée, situation délicate
- IGNORER : newsletter, publicité, notification automatique, email de système, alerte automatique"""

    reponse = requests.post(OLLAMA_URL, json={
        "model": MODELE,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }, timeout=120)

    texte = reponse.json()["message"]["content"]

    try:
        match = re.search(r'\{.*\}', texte, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {
        "classification": "complexe",
        "raison": "Impossible d'analyser automatiquement",
        "resume": "Analyse manuelle requise",
        "reponse_proposee": "",
        "langue": "fr"
    }


# ─────────────────────────────────────────────
# RÉCUPÉRATION DES EMAILS NON LUS
# ─────────────────────────────────────────────
def recuperer_emails_non_lus(service, max_emails=10):
    resultats = service.users().messages().list(
        userId="me",
        labelIds=["UNREAD"],
        maxResults=max_emails
    ).execute()

    messages = resultats.get("messages", [])
    emails = []

    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()
        emails.append({
            "id": msg["id"],
            "contenu": extraire_contenu(detail)
        })

    return emails


# ─────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("📧 Récupération des emails non lus...\n")
    service = connecter_gmail()
    emails = recuperer_emails_non_lus(service, max_emails=10)

    if not emails:
        print("Aucun email non lu.")
    else:
        ignores = 0
        for i, email in enumerate(emails, 1):
            expediteur = email["contenu"]["expediteur"]

            # ── Filtrage rapide sans appeler l'IA ──
            if est_email_automatique(expediteur):
                ignores += 1
                print(f"⏭️  Ignoré (expéditeur automatique) : {email['contenu']['sujet']}")
                continue

            print(f"\n{'─'*50}")
            print(f"Email {i}/{len(emails)}")
            print(f"De      : {expediteur}")
            print(f"Sujet   : {email['contenu']['sujet']}")
            print(f"\n🤖 Analyse en cours...")

            analyse = analyser_email(email["contenu"])

            # ── Résultat selon la classification ──
            if analyse["classification"] == "ignorer":
                ignores += 1
                print(f"⏭️  Ignoré par l'IA : {analyse['raison']}")

            elif analyse["classification"] == "simple":
                print(f"Type    : 🟢 SIMPLE")
                print(f"Raison  : {analyse['raison']}")
                print(f"Résumé  : {analyse['resume']}")
                print(f"\nRéponse proposée :")
                print(f"{analyse['reponse_proposee']}")

            else:
                print(f"Type    : 🟡 COMPLEXE")
                print(f"Raison  : {analyse['raison']}")
                print(f"Résumé  : {analyse['resume']}")
                print(f"\nRéponse proposée (à valider) :")
                print(f"{analyse['reponse_proposee']}")

        if ignores > 0:
            print(f"\n📊 {ignores} email(s) ignoré(s) (newsletters, notifications...)")
