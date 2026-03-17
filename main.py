from connexion import connecter_gmail
from analyseur import recuperer_emails_non_lus, analyser_email, est_email_automatique
from envoi import envoyer_reponse, mettre_en_attente, marquer_comme_lu
import re

# ─────────────────────────────────────────────
# EXTRACTION DE L'ADRESSE EMAIL
# L'expéditeur arrive souvent sous la forme
# "Prénom Nom <email@example.com>"
# On extrait uniquement la partie email.
# ─────────────────────────────────────────────
def extraire_adresse(expediteur):
    match = re.search(r'<(.+?)>', expediteur)
    if match:
        return match.group(1)
    return expediteur.strip()


# ─────────────────────────────────────────────
# TRAITEMENT PRINCIPAL
# Pour chaque email non lu :
# 1. Filtrage rapide
# 2. Analyse par l'IA
# 3. Envoi auto ou mise en attente
# 4. Marquage comme lu
# ─────────────────────────────────────────────
def traiter_emails():
    print("=" * 50)
    print("   EMAIL AI ASSISTANT — Traitement en cours")
    print("=" * 50)

    service = connecter_gmail()
    emails = recuperer_emails_non_lus(service, max_emails=10)

    if not emails:
        print("\n📭 Aucun email non lu. Tout est à jour !")
        return

    print(f"\n📬 {len(emails)} email(s) non lu(s) trouvé(s)\n")

    stats = {"traites": 0, "simples": 0, "complexes": 0, "ignores": 0}

    for email in emails:
        contenu = email["contenu"]
        expediteur = contenu["expediteur"]
        adresse = extraire_adresse(expediteur)

        print(f"{'─' * 50}")
        print(f"De    : {expediteur}")
        print(f"Sujet : {contenu['sujet']}")

        # ── Niveau 1 : filtrage par expéditeur ──
        if est_email_automatique(expediteur):
            print(f"⏭️  Ignoré (expéditeur automatique)")
            marquer_comme_lu(service, email["id"])
            stats["ignores"] += 1
            continue

        # ── Niveau 2 : analyse par l'IA ──
        print("🤖 Analyse en cours...")
        analyse = analyser_email(contenu)

        if analyse["classification"] == "ignorer":
            print(f"⏭️  Ignoré par l'IA : {analyse['raison']}")
            marquer_comme_lu(service, email["id"])
            stats["ignores"] += 1

        elif analyse["classification"] == "simple":
            print(f"🟢 SIMPLE — Envoi automatique de la réponse")
            succes = envoyer_reponse(
                service=service,
                destinataire=adresse,
                sujet=contenu["sujet"],
                corps=analyse["reponse_proposee"]
            )
            if succes:
                marquer_comme_lu(service, email["id"])
                stats["simples"] += 1

        else:
            print(f"🟡 COMPLEXE — Mise en file d'attente pour validation")
            mettre_en_attente(
                email_id=email["id"],
                destinataire=adresse,
                sujet=contenu["sujet"],
                corps_original=contenu["corps"],
                reponse_proposee=analyse["reponse_proposee"]
            )
            marquer_comme_lu(service, email["id"])
            stats["complexes"] += 1

        stats["traites"] += 1
        print()

    # ── Résumé final ──
    print("=" * 50)
    print(f"✅ Traitement terminé !")
    print(f"   🟢 Réponses envoyées automatiquement : {stats['simples']}")
    print(f"   🟡 En attente de validation           : {stats['complexes']}")
    print(f"   ⏭️  Ignorés                            : {stats['ignores']}")
    print("=" * 50)


if __name__ == "__main__":
    traiter_emails()
