import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ─────────────────────────────────────────────
# SCOPES = les permissions qu'on demande à Gmail
# - readonly : lire les emails
# - send : envoyer des emails
# On demande les deux dès maintenant pour ne pas
# avoir à se reconnecter plus tard.
# ─────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send"
]

def connecter_gmail():
    creds = None

    # Si on s'est déjà connecté avant, on réutilise le token sauvegardé
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Si pas de token valide, on lance la connexion dans le navigateur
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expiré → on le renouvelle automatiquement
            creds.refresh(Request())
        else:
            # Première connexion → ouvre le navigateur pour autoriser
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # On sauvegarde le token pour les prochaines fois
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    # On retourne le service Gmail prêt à l'emploi
    service = build("gmail", "v1", credentials=creds)
    return service


def tester_connexion():
    print("🔌 Connexion à Gmail...")
    service = connecter_gmail()

    # On récupère les infos du profil pour vérifier que ça marche
    profil = service.users().getProfile(userId="me").execute()
    print(f"✅ Connecté en tant que : {profil['emailAddress']}")
    print(f"📬 Nombre total de messages : {profil['messagesTotal']}")

    # On récupère les 3 derniers emails non lus pour vérifier
    resultats = service.users().messages().list(
        userId="me",
        labelIds=["UNREAD"],
        maxResults=3
    ).execute()

    messages = resultats.get("messages", [])
    print(f"\n📨 Emails non lus trouvés : {len(messages)}")

    if messages:
        print("\nAperçu des 3 premiers :")
        for msg in messages:
            # On récupère les détails de chaque email
            detail = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["Subject", "From"]
            ).execute()

            headers = detail["payload"]["headers"]
            sujet = next((h["value"] for h in headers if h["name"] == "Subject"), "Sans sujet")
            expediteur = next((h["value"] for h in headers if h["name"] == "From"), "Inconnu")

            print(f"  → De : {expediteur}")
            print(f"     Sujet : {sujet}\n")


if __name__ == "__main__":
    tester_connexion()
