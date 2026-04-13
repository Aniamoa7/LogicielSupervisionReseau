# database.py
import sqlite3
from datetime import datetime

DB_PATH = "supervision.db"

def get_connection():
    """Retourne une connexion à la base de données."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permet d'accéder aux colonnes par nom
    return conn



# CRÉATION DES TABLES


def creer_tables():
    """Crée toutes les tables si elles n'existent pas encore."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table Equipement (correspond à la classe Equipement du diagramme)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL,
            adresse_ip  TEXT NOT NULL UNIQUE,
            type        TEXT NOT NULL,  -- ROUTEUR, SWITCH, SERVEUR, PAREFEU, PC
            statut      TEXT DEFAULT 'ACTIF',  -- ACTIF, INACTIF, CRITIQUE
            derniere_verification DATETIME
        )
    """)

    # Table Metrique (correspond à la classe Metrique du diagramme)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metriques (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            equipement_id   INTEGER NOT NULL,
            type            TEXT NOT NULL,  -- PING, LATENCE
            valeur          REAL,           -- latence en ms, ou 0/1 pour up/down
            unite           TEXT,           -- 'ms' ou 'bool'
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipement_id) REFERENCES equipements(id)
        )
    """)

    # Table Alerte (correspond à la classe Alerte du diagramme)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            equipement_id   INTEGER NOT NULL,
            titre           TEXT NOT NULL,
            description     TEXT,
            niveau          TEXT NOT NULL,  -- P1_CRITIQUE, P2_MAJEUR, P3_MINEUR
            date_creation   DATETIME DEFAULT CURRENT_TIMESTAMP,
            acquittee       INTEGER DEFAULT 0,  -- 0 = non, 1 = oui
            date_acquittement DATETIME,
            FOREIGN KEY (equipement_id) REFERENCES equipements(id)
        )
    """)

    # Table Log (correspond à la classe Log du diagramme)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            equipement_id   INTEGER,
            message         TEXT NOT NULL,
            source          TEXT,           -- quel module a généré ce log
            niveau          TEXT,           -- INFO, WARNING, ERROR
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table Utilisateur (correspond à la classe Utilisateur du diagramme)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            mot_de_passe TEXT NOT NULL,
            role        TEXT DEFAULT 'TECHNICIEN'  -- ADMINISTRATEUR, TECHNICIEN, OBSERVATEUR
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables créées avec succès.")



# FONCTIONS EQUIPEMENTS


def ajouter_equipement(nom, adresse_ip, type_equipement):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO equipements (nom, adresse_ip, type)
        VALUES (?, ?, ?)
    """, (nom, adresse_ip, type_equipement))
    conn.commit()
    conn.close()

def get_tous_equipements():
    conn = get_connection()
    equipements = conn.execute(
        "SELECT * FROM equipements"
    ).fetchall()
    conn.close()
    return equipements

def mettre_a_jour_statut(equipement_id, statut):
    conn = get_connection()
    conn.execute("""
        UPDATE equipements
        SET statut = ?, derniere_verification = ?
        WHERE id = ?
    """, (statut, datetime.now(), equipement_id))
    conn.commit()
    conn.close()



# FONCTIONS METRIQUES


def enregistrer_metrique(equipement_id, type_metrique, valeur, unite):
    conn = get_connection()
    conn.execute("""
        INSERT INTO metriques (equipement_id, type, valeur, unite)
        VALUES (?, ?, ?, ?)
    """, (equipement_id, type_metrique, valeur, unite))
    conn.commit()
    conn.close()

def get_historique_metriques(equipement_id, limite=50):
    conn = get_connection()
    resultats = conn.execute("""
        SELECT * FROM metriques
        WHERE equipement_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (equipement_id, limite)).fetchall()
    conn.close()
    return resultats



# FONCTIONS ALERTES


def creer_alerte(equipement_id, titre, description, niveau):
    conn = get_connection()
    conn.execute("""
        INSERT INTO alertes (equipement_id, titre, description, niveau)
        VALUES (?, ?, ?, ?)
    """, (equipement_id, titre, description, niveau))
    conn.commit()
    conn.close()

def get_alertes_actives():
    conn = get_connection()
    alertes = conn.execute("""
        SELECT a.*, e.nom as equipement_nom, e.adresse_ip
        FROM alertes a
        JOIN equipements e ON a.equipement_id = e.id
        WHERE a.acquittee = 0
        ORDER BY a.date_creation DESC
    """).fetchall()
    conn.close()
    return alertes

def acquitter_alerte(alerte_id):
    conn = get_connection()
    conn.execute("""
        UPDATE alertes
        SET acquittee = 1, date_acquittement = ?
        WHERE id = ?
    """, (datetime.now(), alerte_id))
    conn.commit()
    conn.close()



# FONCTIONS LOGS


def ajouter_log(message, niveau="INFO", source="système", equipement_id=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO logs (equipement_id, message, source, niveau)
        VALUES (?, ?, ?, ?)
    """, (equipement_id, message, source, niveau))
    conn.commit()
    conn.close()

def get_logs_recents(limite=100):
    conn = get_connection()
    logs = conn.execute("""
        SELECT l.*, e.nom as equipement_nom
        FROM logs l
        LEFT JOIN e ON l.equipement_id = e.id
        ORDER BY l.timestamp DESC
        LIMIT ?
    """, (limite,)).fetchall()
    conn.close()
    return logs



# INITIALISATION


if __name__ == "__main__":
    creer_tables()
    print("[DB] Base de données initialisée.")