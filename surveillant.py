import time
import os
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv
from connexion import connecter_gmail
from analyseur import recuperer_emails_non_lus, analyser_email, est_email_automatique
from envoi import envoyer_reponse, mettre_en_attente, marquer_comme_lu
import re

load_dotenv()

INTERVALLE = int(os.getenv("INTERVALLE_MINUTES", 5)) * 60  # en secondes

# ─────────────────────────────────────────────
# LOGGING — toutes les actions sont écrites
# dans logs/activity.log ET affichées dans
# le terminal en temps réel.
# ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/activity.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("surveillant")

# ─────────────────────────────────────────────
# ÉTAT PARTAGÉ
# Ces variables sont lues par l'interface web
# pour afficher le statut en temps réel.
# ─────────────────────────────────────────────
etat = {
    "actif": True,
    "derniere_verification": None,
    "prochaine_verification": None,
    "stats": {
        "simples": 0,
        "complexes": 0,
        "ignores": 0,
        "total_traites": 0
    }
}

# Lock pour éviter les conflits entre threads
lock = threading.Lock()


def extraire_adresse(expediteur):
    match = re.search(r'<(.+?)>', expediteur)
    if match:
        return match.group(1)
    return expediteur.strip()


# ─────────────────────────────────────────────
# NOTIFICATION DESKTOP
# Utilise notify-send (Linux) pour afficher
# une notification système quand un email
# complexe arrive.
# ─────────────────────────────────────────────
def notifier(titre, message):
    try:
        os.system(f'notify-send "{titre}" "{message}" --icon=mail-unread')
    except Exception:
        pass  # Si notify-send n'est pas dispo, on ignore silencieusement


# ─────────────────────────────────────────────
# UN CYCLE DE VÉRIFICATION
# ─────────────────────────────────────────────
def verifier_emails():
    with lock:
        etat["derniere_verification"] = datetime.now().strftime("%H:%M:%S")
        etat["prochaine_verification"] = None

    log.info("─── Début de la vérification ───")

    try:
        service = connecter_gmail()
        emails = recuperer_emails_non_lus(service, max_emails=10)

        if not emails:
            log.info("Aucun email non lu.")
            return

        log.info(f"{len(emails)} email(s) non lu(s) trouvé(s)")

        for email in emails:
            contenu = email["contenu"]
            expediteur = contenu["expediteur"]
            adresse = extraire_adresse(expediteur)

            # Filtrage niveau 1
            if est_email_automatique(expediteur):
                log.info(f"IGNORÉ (auto) | {contenu['sujet']}")
                marquer_comme_lu(service, email["id"])
                with lock:
                    etat["stats"]["ignores"] += 1
                continue

            # Analyse IA
            analyse = analyser_email(contenu)

            if analyse["classification"] == "ignorer":
                log.info(f"IGNORÉ (IA)   | {contenu['sujet']}")
                marquer_comme_lu(service, email["id"])
                with lock:
                    etat["stats"]["ignores"] += 1

            elif analyse["classification"] == "simple":
                succes = envoyer_reponse(service, adresse, contenu["sujet"], analyse["reponse_proposee"])
                if succes:
                    log.info(f"ENVOYÉ        | {contenu['sujet']} → {adresse}")
                    marquer_comme_lu(service, email["id"])
                    with lock:
                        etat["stats"]["simples"] += 1
                        etat["stats"]["total_traites"] += 1

            else:
                mettre_en_attente(
                    email_id=email["id"],
                    destinataire=adresse,
                    sujet=contenu["sujet"],
                    corps_original=contenu["corps"],
                    reponse_proposee=analyse["reponse_proposee"]
                )
                marquer_comme_lu(service, email["id"])
                log.info(f"EN ATTENTE    | {contenu['sujet']} — validation requise")

                # Notification desktop
                notifier(
                    "📧 Email complexe reçu",
                    f"De : {adresse}\n{contenu['sujet']}"
                )

                with lock:
                    etat["stats"]["complexes"] += 1
                    etat["stats"]["total_traites"] += 1

    except Exception as e:
        log.error(f"Erreur lors de la vérification : {e}")

    log.info("─── Fin de la vérification ───")


# ─────────────────────────────────────────────
# BOUCLE PRINCIPALE DE SURVEILLANCE
# Tourne en arrière-plan dans un thread séparé.
# Peut être mise en pause / reprise via l'état.
# ─────────────────────────────────────────────
def boucle_surveillance():
    log.info(f"🚀 Surveillance démarrée — vérification toutes les {INTERVALLE//60} minute(s)")

    while True:
        if etat["actif"]:
            verifier_emails()

            # Calcul de la prochaine vérification
            prochaine = datetime.fromtimestamp(time.time() + INTERVALLE)
            with lock:
                etat["prochaine_verification"] = prochaine.strftime("%H:%M:%S")

            # Attente découpée en petits morceaux
            # pour réagir rapidement à une mise en pause
            for _ in range(INTERVALLE):
                time.sleep(1)
                if not etat["actif"]:
                    break
        else:
            log.info("⏸️  Surveillance en pause...")
            time.sleep(5)


def demarrer_surveillance():
    thread = threading.Thread(target=boucle_surveillance, daemon=True)
    thread.start()
    return thread
