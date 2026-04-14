
try:
    from flask import Flask, render_template, redirect, url_for, abort
except ImportError as exc:
    raise ImportError(
        "Flask doit être installé pour exécuter l'interface web. "
        "Installez-le avec : pip install flask"
    ) from exc

from basedonne import (
    creer_tables,
    ajouter_equipement,
    get_tous_equipements,
    get_historique_metriques
)
from config import EQUIPEMENTS
from alertemanager import lister_alertes_actives, acquitter_alerte_par_id

app = Flask(__name__, template_folder="Template")


def initialiser_base():
    """Crée la base et ajoute les équipements définis dans config.py."""
    creer_tables()
    for eq in EQUIPEMENTS:
        ajouter_equipement(eq["nom"], eq["adresse_ip"], eq["type"])


initialiser_base()


def trouver_equipement(equipement_id):
    """Retourne l'équipement correspondant à l'ID ou None."""
    equipements = get_tous_equipements()
    for eq in equipements:
        if eq["id"] == equipement_id:
            return dict(eq)
    return None


@app.route("/")
def dashboard():
    equipements = [dict(eq) for eq in get_tous_equipements()]
    alertes = lister_alertes_actives()
    return render_template(
        "tabbord.html",
        equipements=equipements,
        alertes=alertes
    )


@app.route("/equipements")
def liste_equipements():
    equipements = [dict(eq) for eq in get_tous_equipements()]
    return render_template(
        "equipement.html",
        equipements=equipements,
        equipement=None,
        metriques=[]
    )


@app.route("/equipement/<int:equipment_id>")
def detail_equipement(equipment_id):
    equipement = trouver_equipement(equipment_id)
    if equipement is None:
        abort(404)

    metriques = get_historique_metriques(equipment_id, limite=20)
    return render_template(
        "equipement.html",
        equipement=equipement,
        metriques=metriques,
        equipements=[]
    )


@app.route("/alertes")
def liste_alertes():
    alertes = lister_alertes_actives()
    return render_template("alerte.html", alertes=alertes)


@app.route("/alertes/acquitter/<int:alerte_id>")
def acquitter_alerte(alerte_id):
    acquitter_alerte_par_id(alerte_id)
    return redirect(url_for("liste_alertes"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
