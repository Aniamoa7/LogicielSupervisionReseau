
try:
    from flask import (
        Flask,
        render_template,
        redirect,
        url_for,
        abort,
        request,
        session,
        flash,
    )
except ImportError as exc:
    raise ImportError(
        "Flask doit être installé pour exécuter l'interface web. "
        "Installez-le avec : pip install flask"
    ) from exc

from werkzeug.security import check_password_hash, generate_password_hash

from basedonne import (
    creer_tables,
    ajouter_equipement,
    get_tous_equipements,
    get_historique_metriques,
    get_utilisateur_par_email,
    get_tous_utilisateurs,
    ajouter_utilisateur,
    count_utilisateurs,
)
from config import EQUIPEMENTS
from alertemanager import lister_alertes_actives, acquitter_alerte_par_id

app = Flask(__name__, template_folder="Template")
app.secret_key = "change_this_secret_key"


def initialiser_base():
    """Crée la base, ajoute les équipements et un utilisateur initial."""
    creer_tables()
    for eq in EQUIPEMENTS:
        ajouter_equipement(eq["nom"], eq["adresse_ip"], eq["type"])

    if count_utilisateurs() == 0:
        mot_de_passe = generate_password_hash("admin")
        ajouter_utilisateur("Administrateur", "admin@localhost", mot_de_passe, role="ADMINISTRATEUR")
        print("[AUTH] Utilisateur par défaut créé : admin@localhost / admin")


initialiser_base()


def trouver_equipement(equipement_id):
    """Retourne l'équipement correspondant à l'ID ou None."""
    equipements = get_tous_equipements()
    for eq in equipements:
        if eq["id"] == equipement_id:
            return dict(eq)
    return None


def user_logged_in():
    return "user_email" in session


def get_current_user():
    if not user_logged_in():
        return None
    return get_utilisateur_par_email(session["user_email"])


def login_required(view):
    def wrapped_view(*args, **kwargs):
        if not user_logged_in():
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view


def admin_required(view):
    def wrapped_view(*args, **kwargs):
        user = get_current_user()
        if user is None or user["role"] != "ADMINISTRATEUR":
            abort(403)
        return view(*args, **kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        mot_de_passe = request.form.get("mot_de_passe", "")
        utilisateur = get_utilisateur_par_email(email)

        if utilisateur is None:
            flash("Email ou mot de passe incorrect.", "danger")
        elif not check_password_hash(utilisateur["mot_de_passe"], mot_de_passe):
            flash("Email ou mot de passe incorrect.", "danger")
        else:
            session["user_email"] = utilisateur["email"]
            flash(f"Connexion réussie. Bienvenue {utilisateur['nom']}.", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("login"))


@app.route("/utilisateurs", methods=["GET", "POST"])
@login_required
@admin_required
def utilisateurs():
    message = None
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        mot_de_passe = request.form.get("mot_de_passe", "")
        role = request.form.get("role", "TECHNICIEN")
        if not nom or not email or not mot_de_passe:
            message = "Tous les champs sont obligatoires."
        else:
            mot_de_passe_hash = generate_password_hash(mot_de_passe)
            ajouter_utilisateur(nom, email, mot_de_passe_hash, role=role)
            message = "Utilisateur ajouté avec succès."
    utilisateurs = [dict(u) for u in get_tous_utilisateurs()]
    return render_template("utilisateurs.html", utilisateurs=utilisateurs, message=message)


@app.context_processor
def inject_user():
    return {
        "user": get_current_user(),
        "user_logged_in": user_logged_in(),
    }


@app.route("/")
@login_required
def dashboard():
    equipements = [dict(eq) for eq in get_tous_equipements()]
    alertes = lister_alertes_actives()
    return render_template(
        "tabbord.html",
        equipements=equipements,
        alertes=alertes
    )


@app.route("/equipements")
@login_required
def liste_equipements():
    equipements = [dict(eq) for eq in get_tous_equipements()]
    return render_template(
        "equipement.html",
        equipements=equipements,
        equipement=None,
        metriques=[]
    )


@app.route("/equipement/<int:equipment_id>")
@login_required
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
@login_required
def liste_alertes():
    alertes = lister_alertes_actives()
    return render_template("alerte.html", alertes=alertes)


@app.route("/alertes/acquitter/<int:alerte_id>")
@login_required
def acquitter_alerte(alerte_id):
    acquitter_alerte_par_id(alerte_id)
    return redirect(url_for("liste_alertes"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
