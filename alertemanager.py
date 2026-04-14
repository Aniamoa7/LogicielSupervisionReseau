
from basedonne import creer_alerte, get_alertes_actives, acquitter_alerte, ajouter_log


def est_alerte_active(equipement_id):
    """Retourne True si une alerte active existe déjà pour l'équipement."""
    alertes = get_alertes_actives()
    return any(alerte["equipement_id"] == equipement_id for alerte in alertes)


def generer_alerte(equipement_id, titre, description, niveau):
    """Crée une alerte si aucune alerte active n'existe pour cet équipement."""
    if est_alerte_active(equipement_id):
        ajouter_log(
            message=f"Alerte déjà active pour l'équipement {equipement_id}",
            niveau="WARNING",
            source="alertemanager",
            equipement_id=equipement_id
        )
        return False

    creer_alerte(equipement_id, titre, description, niveau)
    ajouter_log(
        message=f"Alerte {niveau} créée pour l'équipement {equipement_id}",
        niveau="ERROR",
        source="alertemanager",
        equipement_id=equipement_id
    )
    return True


def lister_alertes_actives():
    """Retourne la liste des alertes actives non acquittées."""
    return get_alertes_actives()


def acquitter_alerte_par_id(alerte_id):
    """Acquitte une alerte en base et enregistre l'opération dans les logs."""
    acquitter_alerte(alerte_id)
    ajouter_log(
        message=f"Alerte {alerte_id} acquittée.",
        niveau="INFO",
        source="alertemanager"
    )
