# superviseur.py

import time
from datetime import datetime
from config import EQUIPEMENTS, INTERVALLE_SUPERVISION, SEUIL_PANNES_CONSECUTIVES, NIVEAUX_ALERTE
from pinger import ping_equipement
from basedonne import (     
    get_tous_equipements,
    mettre_a_jour_statut,
    mettre_a_jour_verification,
    enregistrer_metrique,
    ajouter_log,
)
from alertemanager import generer_alerte, lister_alertes_actives

# ─────────────────────────────────────────
# MÉMOIRE DES ÉCHECS CONSÉCUTIFS
# dictionnaire { equipement_id : nb_echecs }
# correspond au SEUIL du diagramme d'activité
# ─────────────────────────────────────────
compteur_echecs = {}


def initialiser_equipements():
    """
    Au démarrage, charge tous les équipements depuis config.py
    et les insère dans la base de données s'ils n'existent pas.
    Correspond à 'Chargement de la liste des équipements'
    dans le diagramme d'activité.
    """
    from basedonne import ajouter_equipement
    print("[SUPERVISEUR] Initialisation des équipements...")
    for eq in EQUIPEMENTS:
        ajouter_equipement(eq["nom"], eq["adresse_ip"], eq["type"])
        print(f"  ✓ {eq['nom']} ({eq['adresse_ip']}) enregistré")
    print("[SUPERVISEUR] Initialisation terminée.\n")


def analyser_resultat(equipement, resultat_ping):
    """
    Analyse le résultat d'un ping et décide quoi faire.
    Correspond au bloc de décision 'Équipement répond ?'
    dans le diagramme d'activité.
    """
    eq_id   = equipement["id"]
    eq_nom  = equipement["nom"]
    eq_ip   = equipement["adresse_ip"]
    eq_type = equipement["type"]

    # initialiser le compteur si premier passage
    if eq_id not in compteur_echecs:
        compteur_echecs[eq_id] = 0

    if resultat_ping["succes"]:
        # ── équipement répond ──────────────────
        compteur_echecs[eq_id] = 0  # reset du compteur

        mettre_a_jour_statut(eq_id, "ACTIF")
        enregistrer_metrique(eq_id, "PING", 1, "bool")

        if resultat_ping["latence"] is not None:
            enregistrer_metrique(
                eq_id, "LATENCE", resultat_ping["latence"], "ms")

        print(f"  [OK] {eq_nom} ({eq_ip}) "
              f"- latence : {resultat_ping['latence']} ms")

    else:
        # ── équipement ne répond pas ───────────
        compteur_echecs[eq_id] += 1
        nb = compteur_echecs[eq_id]

        enregistrer_metrique(eq_id, "PING", 0, "bool")
        mettre_a_jour_verification(eq_id)
        print(f"  [ECHEC] {eq_nom} ({eq_ip}) "
              f"- échec {nb}/{SEUIL_PANNES_CONSECUTIVES}")

        if nb >= SEUIL_PANNES_CONSECUTIVES:
            # seuil atteint → créer une alerte
            niveau = NIVEAUX_ALERTE.get(eq_type, "P3_MINEUR")
            mettre_a_jour_statut(eq_id, "INACTIF")
            if generer_alerte(
                equipement_id=eq_id,
                titre=f"Panne détectée : {eq_nom}",
                description=(
                    f"L'équipement {eq_nom} ({eq_ip}) ne répond plus "
                    f"depuis {nb} tentatives consécutives."
                ),
                niveau=niveau
            ):
                print(f"  [ALERTE {niveau}] Panne enregistrée pour {eq_nom} !")
            else:
                print(f"  [ALERTE] Une alerte active existe déjà pour {eq_nom}.")
            # reset pour ne pas créer une alerte à chaque cycle
            compteur_echecs[eq_id] = 0


def cycle_supervision():
    """
    Un cycle complet de supervision — ping tous les équipements.
    Correspond à une itération de la boucle 'loop toutes les 30s'
    dans le diagramme de séquence.
    """
    equipements = get_tous_equipements()
    maintenant  = datetime.now().strftime("%H:%M:%S")

    print(f"\n{'='*50}")
    print(f"[CYCLE] {maintenant} - supervision de "
          f"{len(equipements)} équipements")
    print(f"{'='*50}")

    for eq in equipements:
        # convertir Row sqlite en dict pour faciliter l'accès
        eq = dict(eq)
        resultat = ping_equipement(eq["adresse_ip"])
        analyser_resultat(eq, resultat)

    # afficher les alertes actives à la fin du cycle
    alertes = lister_alertes_actives()
    if alertes:
        print(f"\n  ⚠️  {len(alertes)} alerte(s) active(s) non acquittée(s)")


def demarrer():
    """
    Point d'entrée principal — boucle infinie de supervision.
    Correspond à 'Démarrage du système' dans le diagramme d'activité.
    """
    print("="*50)
    print("  SYSTÈME DE SUPERVISION RÉSEAU")
    print("  Démarrage...")
    print("="*50)

    # étape 1 : initialiser la base et les équipements
    from basedonne import creer_tables
    creer_tables()
    initialiser_equipements()

    ajouter_log(
        message="Système de supervision démarré",
        niveau="INFO",
        source="superviseur"
    )

    # étape 2 : boucle infinie
    # correspond à 'repeat while Supervision active ?'
    # dans le diagramme d'activité
    try:
        while True:
            cycle_supervision()
            print(f"\n[ATTENTE] Prochain cycle dans "
                  f"{INTERVALLE_SUPERVISION} secondes...")
            time.sleep(INTERVALLE_SUPERVISION)

    except KeyboardInterrupt:
        # Ctrl+C pour arrêter proprement
        print("\n\n[SUPERVISEUR] Arrêt du système...")
        ajouter_log(
            message="Système de supervision arrêté manuellement",
            niveau="INFO",
            source="superviseur"
        )
        print("[SUPERVISEUR] Au revoir !")


# ─────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────

if __name__ == "__main__":
    demarrer()