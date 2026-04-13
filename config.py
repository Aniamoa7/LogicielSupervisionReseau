# config.py

# ─────────────────────────────────────────
# PARAMÈTRES GÉNÉRAUX
# ─────────────────────────────────────────

INTERVALLE_SUPERVISION = 30        # secondes entre chaque cycle de ping
SEUIL_PANNES_CONSECUTIVES = 3      # nb d'échecs avant de créer une alerte
TIMEOUT_PING = 1                   # secondes avant de considérer un ping échoué
DB_PATH = "supervision.db"

# ─────────────────────────────────────────
# ÉQUIPEMENTS DE LA PETITE ENTREPRISE
# (réseau fictif 192.168.1.0/24)
# ─────────────────────────────────────────

EQUIPEMENTS = [
    {
        "nom": "Routeur Principal",
        "adresse_ip": "192.168.1.1",
        "type": "ROUTEUR"
    },
    {
        "nom": "Switch Coeur",
        "adresse_ip": "192.168.1.2",
        "type": "SWITCH"
    },
    {
        "nom": "Serveur Web",
        "adresse_ip": "192.168.1.10",
        "type": "SERVEUR"
    },
    {
        "nom": "Serveur Fichiers",
        "adresse_ip": "192.168.1.11",
        "type": "SERVEUR"
    },
    {
        "nom": "PC Comptabilite",
        "adresse_ip": "192.168.1.20",
        "type": "PC"
    },
    {
        "nom": "PC Direction",
        "adresse_ip": "192.168.1.21",
        "type": "PC"
    },
    {
        "nom": "PC Technicien",
        "adresse_ip": "192.168.1.22",
        "type": "PC"
    },
    {
        "nom": "Imprimante Reseau",
        "adresse_ip": "192.168.1.30",
        "type": "IMPRIMANTE"
    },
]

# ─────────────────────────────────────────
# NIVEAUX D'ALERTE
# (correspond aux NiveauAlerte du diagramme de classes)
# ─────────────────────────────────────────

NIVEAUX_ALERTE = {
    "ROUTEUR":    "P1_CRITIQUE",   # routeur tombe = tout le réseau mort
    "SWITCH":     "P1_CRITIQUE",
    "SERVEUR":    "P2_MAJEUR",
    "PC":         "P3_MINEUR",
    "IMPRIMANTE": "P3_MINEUR",
}