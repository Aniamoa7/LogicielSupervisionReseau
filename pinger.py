# pinger.py

import subprocess
import platform
import time
from config import TIMEOUT_PING


def ping_equipement(adresse_ip):
    """
    Envoie un ping ICMP à l'adresse IP donnée.
    Retourne un dictionnaire avec :
        - succes (bool)   : True si l'équipement répond
        - latence (float) : temps de réponse en ms, None si échec
        - timestamp       : moment du ping
    """

    # la commande ping est différente selon l'OS
    # Windows : ping -n 1 -w 1000 192.168.1.1
    # Linux/Mac : ping -c 1 -W 1 192.168.1.1
    systeme = platform.system().lower()

    if systeme == "windows":
        commande = ["ping", "-n", "1", "-w",
                    str(TIMEOUT_PING * 1000), adresse_ip]
    else:
        commande = ["ping", "-c", "1", "-W",
                    str(TIMEOUT_PING), adresse_ip]

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        # on lance la commande ping et on capture la sortie
        resultat = subprocess.run(
            commande,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_PING + 2
        )

        if resultat.returncode == 0:
            # ping réussi → on extrait la latence
            latence = extraire_latence(resultat.stdout, systeme)
            return {
                "succes": True,
                "latence": latence,
                "timestamp": timestamp,
                "adresse_ip": adresse_ip
            }
        else:
            # ping échoué → équipement ne répond pas
            return {
                "succes": False,
                "latence": None,
                "timestamp": timestamp,
                "adresse_ip": adresse_ip
            }

    except subprocess.TimeoutExpired:
        return {
            "succes": False,
            "latence": None,
            "timestamp": timestamp,
            "adresse_ip": adresse_ip
        }


def extraire_latence(output, systeme):
    """
    Extrait la latence en ms depuis la sortie texte du ping.
    Retourne un float ou None si extraction impossible.
    """
    try:
        if systeme == "windows":
            # sortie Windows contient "Moyenne = Xms" ou "Average = Xms"
            for mot in ["Moyenne", "Average"]:
                if mot in output:
                    partie = output.split(mot + " = ")[1]
                    latence = partie.split("ms")[0].strip()
                    return float(latence)
        else:
            # sortie Linux contient "time=X.XX ms"
            if "time=" in output:
                partie = output.split("time=")[1]
                latence = partie.split(" ms")[0].strip()
                return float(latence)
    except:
        pass
    return None


def tester_connectivite(adresse_ip, nb_essais=3):
    """
    Teste la connectivité plusieurs fois pour éviter les faux positifs.
    Correspond au SEUIL_PANNES_CONSECUTIVES du diagramme d'activité.
    Retourne True si au moins un ping réussit sur nb_essais.
    """
    for i in range(nb_essais):
        resultat = ping_equipement(adresse_ip)
        if resultat["succes"]:
            return True
        time.sleep(1)
    return False


# ─────────────────────────────────────────
# TEST DIRECT DU MODULE
# ─────────────────────────────────────────

if __name__ == "__main__":
    # pour tester, on ping Google et une IP fictive
    print("Test ping Google (8.8.8.8)...")
    r = ping_equipement("8.8.8.8")
    print(f"  Succès : {r['succes']} | Latence : {r['latence']} ms")

    print("\nTest ping IP inexistante (192.168.1.99)...")
    r = ping_equipement("192.168.1.99")
    print(f"  Succès : {r['succes']} | Latence : {r['latence']}")