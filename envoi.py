import base64
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from connexion import connecter_gmail

# ─────────────────────────────────────────────
# FILE D'ATTENTE DES EMAILS COMPLEXES
# Les emails complexes ne sont pas envoyés
# automatiquement. On les stocke dans un fichier
# JSON en attendant la validation humaine.
# ─────────────────────────────────────────────
FILE_ATTENTE = "file_attente.json"

def charger_file_attente():
    if os.path.exists(FILE_ATTENTE):
        with open(FILE_ATTENTE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_file_attente(file):
    with open(FILE_ATTENTE, "w", encoding="utf-8") as f:
        json.dump(file, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# CONSTRUCTION D'UN EMAIL
# On crée un email au format MIME (le format
# standard des emails) puis on l'encode en
# base64 pour l'envoyer via l'API Gmail.
# ─────────────────────────────────────────────
def construire_email(destinataire, sujet, corps):
    message = MIMEMultipart()
    message["to"] = destinataire
    message["subject"] = f"Re: {sujet}"

    # On ajoute le corps en texte brut
    message.attach(MIMEText(corps, "plain", "utf-8"))

    # Encodage base64 requis par l'API Gmail
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


# ─────────────────────────────────────────────
# ENVOI AUTOMATIQUE (emails simples)
# ─────────────────────────────────────────────
def envoyer_reponse(service, destinataire, sujet, corps):
    try:
        email = construire_email(destinataire, sujet, corps)
        service.users().messages().send(
            userId="me",
            body=email
        ).execute()
        print(f"  ✅ Réponse envoyée à : {destinataire}")
        return True
    except Exception as e:
        print(f"  ❌ Erreur d'envoi : {e}")
        return False


# ─────────────────────────────────────────────
# MISE EN FILE D'ATTENTE (emails complexes)
# ─────────────────────────────────────────────
def mettre_en_attente(email_id, destinataire, sujet, corps_original, reponse_proposee):
    file = charger_file_attente()

    # On vérifie que cet email n'est pas déjà en attente
    ids_existants = [e["email_id"] for e in file]
    if email_id in ids_existants:
        print(f"  ⏭️  Déjà en file d'attente")
        return

    file.append({
        "email_id": email_id,
        "destinataire": destinataire,
        "sujet": sujet,
        "corps_original": corps_original,
        "reponse_proposee": reponse_proposee,
        "statut": "en_attente"  # en_attente / approuve / rejete
    })

    sauvegarder_file_attente(file)
    print(f"  📥 Mis en file d'attente pour validation")


# ─────────────────────────────────────────────
# MARQUER UN EMAIL COMME LU
# Après traitement, on retire le label UNREAD
# pour ne pas le retraiter au prochain passage.
# ─────────────────────────────────────────────
def marquer_comme_lu(service, email_id):
    try:
        service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except Exception as e:
        print(f"  ⚠️  Impossible de marquer comme lu : {e}")


# ─────────────────────────────────────────────
# TEST DU MODULE
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 Test du module d'envoi\n")
    service = connecter_gmail()

    # Test 1 : mise en file d'attente
    print("Test 1 — Mise en file d'attente d'un email complexe :")
    mettre_en_attente(
        email_id="test_123",
        destinataire="test@example.com",
        sujet="Commande non reçue",
        corps_original="J'ai commandé il y a 10 jours et rien reçu.",
        reponse_proposee="Nous sommes désolés, nous enquêtons sur votre commande."
    )

    # Test 2 : affichage de la file d'attente
    print("\nTest 2 — Contenu de la file d'attente :")
    file = charger_file_attente()
    for item in file:
        print(f"  → {item['sujet']} | {item['destinataire']} | {item['statut']}")

    print("\n✅ Module d'envoi opérationnel !")
    print("   Le vrai envoi sera testé depuis l'interface web.")
