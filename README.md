Email : admin@localhost
Mot de passe : admin

Étape 1 — database.py + config.py : créer la base de données et définir les équipements fictifs. C'est le socle de tout.
Étape 2 — pinger.py : la fonction qui ping une IP et retourne True/False + latence.
Étape 3 — supervisor.py : la boucle qui tourne toutes les X secondes, appelle le pinger sur chaque équipement, stocke les résultats, détecte les pannes.
Étape 4 — alert_manager.py : créer une alerte quand une panne est détectée.
Étape 5 — app.py + templates HTML : l'interface web Flask qui lit la base et affiche le dashboard.

On commence par le Module 1 — database.py
C'est quoi ce module et pourquoi il existe ?
C'est le seul module qui parle à la base de données. Tous les autres modules (pinger, supervisor, etc.) ne touchent jamais directement à SQLite — ils appellent des fonctions de database.py. C'est ce qu'on appelle une couche d'abstraction : si demain tu veux passer de SQLite à MySQL, tu modifies uniquement ce fichier, rien d'autre.
Il correspond dans les diagrammes à la classe BaseDeDonnees et aux classes Equipement, Metrique, Alerte, Log, Utilisateur du diagramme de classes.
Ce module fait deux choses : créer les tables au démarrage, et fournir toutes les fonctions CRUD (Create, Read, Update, Delete).

C'est quoi config.py et pourquoi il existe ?
C'est le fichier qui centralise toutes les constantes et paramètres du système. Au lieu d'écrire les IPs et les seuils directement dans le code (ce qu'on appelle du "hardcoding"), on les met ici. Comme ça si tu veux changer un paramètre, tu modifies un seul endroit.
Il correspond dans les diagrammes à la liste des équipements de la classe Equipement et aux seuils mentionnés dans le diagramme d'activité (Seuil critique atteint ?).
Exactement ! C'est tout l'intérêt de ce module. Tu veux ajouter un équipement ? Tu rajoutes juste un bloc dans la liste EQUIPEMENTS :
python{
    "nom": "PC RH",
    "adresse_ip": "192.168.1.23",
    "type": "PC"
},
Et tout le reste du code s'adapte automatiquement — le superviseur va automatiquement commencer à pinger cette nouvelle IP, la base de données va enregistrer ses métriques, l'interface web va l'afficher. Tu touches à rien d'autre.

C'est ce qu'on appelle le principe "Open/Closed" en génie logiciel — ton système est ouvert à l'extension (ajouter des équipements) mais fermé à la modification (tu changes pas la logique du code). C'est exactement le genre de concept que ta prof veut voir appliqué.

C'est quoi pinger.py et pourquoi il existe ?
C'est le module qui fait une seule chose : envoyer un ping ICMP à une adresse IP et retourner le résultat. Rien de plus. Il correspond dans les diagrammes à l'Agent ICMP du diagramme de composants et à la méthode ping() de la classe Equipement.
Le principe : ton OS a déjà une commande ping intégrée — Python va juste l'appeler et interpréter le résultat.
La fonction ping_equipement() retourne un dictionnaire propre que superviseur.py va utiliser directement pour décider si un équipement est UP ou DOWN, et que basedonne.py va enregistrer dans la table metriques.

-C'est quoi superviseur.py et pourquoi il existe ?C'est le cerveau du système — le module principal qui orchestre tout. Il tourne en boucle infinie, appelle pinger.py pour chaque équipement, enregistre les résultats dans la base via basedonne.py, et décide si une alerte doit être créée. Il correspond exactement au Moteur de Supervision dans le diagramme de composants et à la boucle principale du diagramme de séquence (loop toutes les 30 secondes).

Pour tester maintenant
bashpython superviseur.py
Tu vas voir quelque chose comme :
==================================================
  SYSTÈME DE SUPERVISION RÉSEAU
  Démarrage...
==================================================
[SUPERVISEUR] Initialisation des équipements...
  ✓ Routeur Principal (192.168.1.1) enregistré
  ✓ Switch Coeur (192.168.1.2) enregistré
  ...

==================================================
[CYCLE] 14:32:01 - supervision de 8 équipements
==================================================
  [ECHEC] Routeur Principal (192.168.1.1) - échec 1/3
  [ECHEC] Switch Coeur (192.168.1.2) - échec 1/3
  [OK] 8.8.8.8 - latence : 12.0 ms
  ...
Les équipements fictifs vont tous échouer (normal, les IPs n'existent pas sur ton réseau), mais c'est exactement ce qu'on veut voir — le système détecte les pannes et crée les alertes après 3 échecs consécutifs.


"""
Gestion des alertes du système de supervision.

Ce module encapsule la logique métier pour créer, lister et acquitter
les alertes sans que les autres modules accèdent directement aux
fonctions bas niveau de la base de données.
Objectif du module alertemanager.py
Le but principal de alertemanager.py est de centraliser toute la logique liée aux alertes.

Il transforme une panne détectée en action métier (créer alerte, vérifier si alerte existe déjà, acquitter alerte).
Il évite que superviseur.py fasse directement des opérations de base de données sur les alertes.
Il sert de couche intermédiaire entre la supervision et la base de données.
Pourquoi on utilise ce module
On l’utilise pour respecter le principe de séparation des responsabilités :

superviseur.py : fait la supervision réseau, décide quand il y a un problème.
alertemanager.py : gère uniquement les règles et le traitement des alertes.
basedonne.py : exécute réellement les opérations SQLite.
C’est important parce que :

le code est plus propre
plus simple à maintenir
plus facile à modifier si on change la façon dont on gère les alertes
plus facile à tester séparément
Comment il fonctionne en arrière-plan
1. Superviseur détecte une panne
Quand superviseur.py voit qu’un équipement n’a pas répondu pendant SEUIL_PANNES_CONSECUTIVES cycles, il appelle :

generer_alerte(...)
2. alertemanager.py vérifie l’alerte active
Dans generer_alerte, il fait d’abord :

est_alerte_active(equipement_id)
Cette fonction appelle la base de données via get_alertes_actives() pour savoir si une alerte non acquittée existe déjà pour cet équipement.

3. Création d’alerte si besoin
Si aucune alerte active n’existe :

il appelle creer_alerte(...) depuis basedonne.py
il écrit aussi un log via ajouter_log(...)
Si une alerte est déjà active :

il ne recrée rien
il ajoute un log de type WARNING
4. Liste des alertes actives
lister_alertes_actives() retourne simplement les alertes non acquittées.

5. Acquittement d’une alerte
acquitter_alerte_par_id(alerte_id) :

appelle acquitter_alerte() en base
ajoute un log pour garder la trace
Son rôle dans la structure du projet
Dans l’architecture globale, alertemanager.py est la couche métier entre :

superviseur.py (qui orchestre la surveillance)
basedonne.py (qui stocke les données)
Schéma simplifié :

config.py : paramètres et seuils
pinger.py : ping / réponse réseau
superviseur.py : boucle, décision de panne
alertemanager.py : règles d’alerte, état des alertes
basedonne.py : persistance SQLite
En résumé
alertemanager.py est utile parce que :

il sépare la logique d’alerte de la logique de supervision
il évite qu’on crée plusieurs fois la même alerte
il garde la base propre en n’écrivant que ce qui est nécessaire
il facilite l’évolution du projet si tu veux ajouter par exemple :
une notification e-mail
un envoi Slack
un système d’escalade
Si tu veux, je peux aussi t’expliquer comment ajouter une fonction de notification (mail/Slack) dans alertemanager.py.

Raptor mini (Preview) • 1x


appli.py module; 
Interface web de supervision.

Ce fichier démarre une application Flask qui permet de :
- afficher le dashboard de supervision
- lister les équipements et leur statut
- afficher les alertes actives
- acquitter une alerte depuis l'interface
But de appli.py
appli.py est le point d’entrée de l’interface web de ton logiciel de supervision.

Il permet de transformer le système de supervision en application web accessible depuis un navigateur.
Sans ce fichier, ton projet ne serait qu’un programme qui tourne en console et enregistre des données dans SQLite.
Rôle de appli.py
1. Démarrer le serveur web
Il crée un objet Flask : app = Flask(__name__, template_folder="Template")
Cela signifie que l’application web va servir des pages HTML depuis le dossier Template
2. Afficher les vues principales
Il définit plusieurs routes HTTP :

/ → page d’accueil / dashboard
/equipements → liste des équipements supervisés
/equipement/<id> → détail d’un équipement + historique des métriques
/alertes → liste des alertes actives
/alertes/acquitter/<id> → action pour acquitter une alerte
Pourquoi appli.py existe
C’est le fichier qui fait le lien entre :

la base de données (basedonne.py)
la logique des alertes (alertemanager.py)
les templates HTML
et l’utilisateur qui consulte le système depuis un navigateur
Sans appli.py, tu aurais bien les données et la supervision, mais pas de tableau de bord ni d’interface utilisateur.

Comment il fonctionne en arrière-plan
appli.py importe les fonctions utiles :

get_tous_equipements() et get_historique_metriques() depuis basedonne.py
lister_alertes_actives() et acquitter_alerte_par_id() depuis alertemanager.py
Quand un visiteur ouvre une page :

Flask appelle la fonction correspondante (dashboard(), liste_equipements(), etc.)
cette fonction récupère des données en base
puis retourne une page HTML générée avec render_template(...)
Pour acquitter une alerte :

la route /alertes/acquitter/<id> appelle acquitter_alerte_par_id()
puis redirige vers la page des alertes
En résumé
appli.py existe pour que ton logiciel de supervision soit :

utilisable via un navigateur
plus facile à consulter
capable d’afficher les équipements et alertes en temps réel
capable de piloter l’application depuis une interface graphique simple
Si tu veux, je peux aussi expliquer comment fonctionne le template tabbord.html avec appli.py.

Raptor mini (Preview) • 1x

Les fichiers html:


Rôle global des fichiers HTML
Ces fichiers sont les vues de l’interface web Flask.

Ils ne contiennent pas la logique métier.
Ils affichent les données envoyées par appli.py.
Ils utilisent le moteur de template Jinja de Flask ({{ ... }} et {% ... %}).
Chaque template correspond à une page différente du site.

Template/tabbord.html
But
Afficher le tableau de bord principal.
Ce qu’il sert à montrer
la liste des équipements supervisés
le statut de chaque équipement
les alertes actives en cours
Son rôle dans la structure
C’est la page d’accueil de l’application web
Elle permet de voir rapidement l’état du système
Elle relie les pages équipements et alertes avec des liens
Template/equipement.html
But
Afficher soit la liste complète des équipements,
soit le détail d’un seul équipement.
Ce qu’il sert à montrer
si equipement est absent : liste des équipements
si equipement est présent : détail de l’équipement et son historique de métriques
Son rôle dans la structure
C’est une page polyvalente
Elle évite de créer deux templates séparés pour la liste et le détail
Elle rend l’interface plus simple à maintenir
Template/alerte.html
But
Afficher les alertes actives non acquittées
Ce qu’il sert à montrer
chaque alerte active
le niveau, la date et l’équipement concerné
un lien pour acquitter l’alerte
Son rôle dans la structure
C’est la page dédiée au suivi des problèmes
Elle permet de visualiser les incidents en cours
Elle rend possible l’action de nettoyage via l’interface
En résumé
tabbord.html = vue générale, dashboard
equipement.html = équipements + détails
alerte.html = suivi et acquittement des alertes
Ces fichiers sont indispensables pour que ton projet ne soit pas seulement un programme console, mais un vrai tableau de bord web.

ICIIIIIIIIIII
================================================================================
PLAN DE MISE EN ŒUVRE : TEST AVEC 4 VMs EN MODE BRIDGED + ROUTEUR PHYSIQUE
================================================================================

OBJECTIF GLOBAL :
Créer un environnement de test réaliste avec 4 VMs en mode Bridged connectées au routeur physique,
puis valider que le logiciel de supervision (tournant sur la machine hôte Windows) détecte correctement
les pannes, crée les alertes, et affiche les résultats sur le dashboard web.

================================================================================
PHASE 1 : PRÉPARATION DE L'INFRASTRUCTURE RÉSEAU (ROUTEUR PHYSIQUE + VMs BRIDGED)
================================================================================

⚠️ POINT IMPORTANT : Les VMs n'ont PAS besoin de Python installé !
   Elles doivent simplement répondre aux pings ICMP (c'est automatique).
   Vous allez configurer des IPs statiques et laisser le système répondre aux requêtes.

ÉTAPE 1.1 : Créer 4 VMs dans VMware Workstation
─────────────────────────────────────────────

Actions à faire :
  1. Ouvrir VMware Workstation
  2. Créer 4 VMs avec les caractéristiques minimales :
     - VM1 : "Serveur-Web" (Ubuntu Server ou Debian)
     - VM2 : "Serveur-BD" (Ubuntu Server ou Debian)
     - VM3 : "Client-Compta" (Ubuntu Server ou Debian)
     - VM4 : "Client-Admin" (Ubuntu Server ou Debian)
  
  Ressources recommandées par VM :
     - vCPU : 1-2
     - Mémoire : 512 Mo - 1 Go (minimal suffit)
     - Disque : 10-20 Go
  
  ISO à utiliser :
     - Ubuntu Server 22.04 LTS ✓ recommandé (léger, gratuit, pas d'interface graphique)
     - Debian 11 ou 12
  
Installation rapide :
  - Installer avec les valeurs par défaut
  - Choisir une installation MINIMALE (pas de packages supplémentaires)
  - Créer un compte utilisateur simple (ex: user/user)
  - ✓ Pas besoin d'installer Python, services, ou dépendances

Résultat attendu :
  ✓ 4 VMs démarrées et accessibles via SSH
  ✓ Chaque VM peut être pingée
  ✓ Chaque VM a un utilisateur de connexion

─────────────────────────────────────────────

ÉTAPE 1.2 : Configurer le mode BRIDGED sur chaque VM
────────────────────────────────────────────────

Actions à faire (Dans VMware Workstation, pour chaque VM) :
  1. Sélectionner la VM
  2. Clic-droit → "Settings" (ou Edit → Virtual Machine Settings)
  3. Dans l'onglet "Hardware" → "Network Adapter"
  4. Changer le mode réseau :
     Avant : "NAT" ou "Host-only"
     Après : "Bridged"
  5. Sélectionner l'adaptateur réseau physique :
     → Choisir celui qui est connecté au routeur physique
  6. Cliquer "OK"
  7. Répéter pour les 4 VMs

Résultat attendu :
  ✓ Les 4 VMs sont en mode Bridged
  ✓ Chaque VM aura une IP du même réseau que votre PC hôte

─────────────────────────────────────────────

ÉTAPE 1.3 : Brancher votre PC au routeur physique
──────────────────────────────────────────────

Actions à faire :
  1. Brancher votre machine hôte au routeur physique avec un câble Ethernet
     (ou Wi-Fi si le routeur supporte)
  
  2. Vérifier que vous recevez une adresse IP du routeur :
     Windows PowerShell :
     $ ipconfig | grep -A 5 "Ethernet"
     
     Vous devez voir une adresse IP du routeur (ex: 192.168.2.10)
  
  3. Noter l'adresse IP de votre PC hôte (vous en aurez besoin plus tard)

Résultat attendu :
  ✓ Votre PC reçoit une IP du routeur (ex: 192.168.2.10)
  ✓ Vous avez une connectivité réseau

─────────────────────────────────────────────

ÉTAPE 1.4 : Démarrer les VMs et récupérer leurs IPs
────────────────────────────────────────────────

Actions à faire :
  1. Démarrer les 4 VMs (clic sur le bouton "Power On" dans VMware)
  2. Attendre qu'elles soient complètement démarrées (~1-2 minutes par VM)
  3. Sur chaque VM, se connecter et obtenir l'IP :
     
     Depuis la console ou SSH :
     $ ip addr show | grep "inet" | grep -v "127.0.0.1"
     
     Vous devez voir une adresse IP du routeur (ex: 192.168.2.100)

NOTA : Les IPs sont actuellement en DHCP (dynamiques).
Vous allez les rendre statiques à l'étape suivante.

Résultat attendu :
  ✓ VM1 a une IP (ex: 192.168.2.100)
  ✓ VM2 a une IP (ex: 192.168.2.101)
  ✓ VM3 a une IP (ex: 192.168.2.102)
  ✓ VM4 a une IP (ex: 192.168.2.103)

─────────────────────────────────────────────

ÉTAPE 1.5 : Configurer les IPs statiques sur les VMs
────────────────────────────────────────────────

Sur chaque VM, identifiez d'abord votre configuration :
  $ sudo nano /etc/netplan/00-installer-config.yaml

Exemple de contenu AVANT (DHCP dynamique) :
  ─────────────────────────────────────────────
  network:
    version: 2
    ethernets:
      eth0:
        dhcp4: true
  ─────────────────────────────────────────────

Contenu à REMPLACER PAR (IPs statiques) :
  ─────────────────────────────────────────────
  network:
    version: 2
    ethernets:
      eth0:
        dhcp4: false
        addresses:
          - 192.168.2.101/24        ← Pour VM1
          - 192.168.2.102/24        ← Pour VM2
          - 192.168.2.103/24        ← Pour VM3
          - 192.168.2.104/24        ← Pour VM4
        gateway4: 192.168.2.1       (demander l'IP de la passerelle à votre routeur)
        nameservers:
          addresses: [8.8.8.8, 8.8.4.4]  (optionnel, juste pour DNS externes)
  ─────────────────────────────────────────────

Après avoir modifié le fichier :
  $ sudo netplan apply
  $ ip addr show          ← vérifier que l'IP est bien statique

Répéter pour chaque VM avec une IP différente.

Résultat attendu :
  ✓ VM1 a l'IP statique 192.168.2.101
  ✓ VM2 a l'IP statique 192.168.2.102
  ✓ VM3 a l'IP statique 192.168.2.103
  ✓ VM4 a l'IP statique 192.168.2.104

─────────────────────────────────────────────

ÉTAPE 1.6 : Tester la connectivité réseau
──────────────────────────────────────────

Depuis votre machine hôte (Windows), ouvrir PowerShell :

  $ ping 192.168.2.101
  $ ping 192.168.2.102
  $ ping 192.168.2.103
  $ ping 192.168.2.104

Résultat attendu :
  ✓ Tous les pings réussissent avec une latence 1-5 ms
  ✓ 0 % de perte de paquets
  ✓ Les VMs répondent correctement

Si les pings ne passent pas → vérifier :
  1. Les 4 VMs sont-elles démarrées ?
  2. Les IPs statiques sont-elles bien configurées ?
  3. Votre PC hôte et les VMs sont-elles sur le même réseau du routeur ?
  4. Le routeur physique fonctionne-t-il ?
  5. Les VMs sont-elles bien en mode Bridged dans VMware ?

================================================================================
PHASE 2 : ADAPTATION DU LOGICIEL DE SUPERVISION (SUR LA MACHINE HÔTE WINDOWS)
================================================================================

⚠️ RAPPEL IMPORTANT : 
  - Aucune dépendance Python à installer sur les VMs
  - Le logiciel tourne UNIQUEMENT sur votre PC Windows
  - Les VMs ne font que répondre aux pings (automatique au niveau OS)

ÉTAPE 2.1 : Vérifier les dépendances sur la machine hôte
─────────────────────────────────────────────────────

Sur votre PC Windows, ouvrir PowerShell et vérifier :

  $ python --version
  $ pip list | grep -i flask

Si Flask n'est pas installé :
  $ pip install flask

Autres packages (généralement déjà inclus) :
  $ pip install sqlite3   (est habituellement inclus par défaut)

Résultat attendu :
  ✓ Python 3.x est disponible sur votre PC
  ✓ Flask est installé
  ✓ SQLite3 est disponible

─────────────────────────────────────────────────────

ÉTAPE 2.2 : Sauvegarder la version actuelle de config.py
─────────────────────────────────────────────────────

Avant de modifier config.py, créer une copie :
  - Dupliquer config.py → config_BACKUP.py (pour revenir en arrière si besoin)

─────────────────────────────────────────────────────

ÉTAPE 2.3 : Mettre à jour config.py avec les vraies IPs des VMs
─────────────────────────────────────────────────────────────

Ouvrir [config.py](config.py) et remplacer les équipements fictifs :

AVANT :
  EQUIPEMENTS = [
      {"nom": "Routeur Principal", "adresse_ip": "192.168.1.1", "type": "ROUTEUR"},
      {"nom": "Switch Coeur", "adresse_ip": "192.168.1.2", "type": "SWITCH"},
      ...
  ]

APRÈS (avec les vraies IPs des VMs) :
  EQUIPEMENTS = [
      {"nom": "Serveur-Web", "adresse_ip": "192.168.2.101", "type": "SERVEUR"},
      {"nom": "Serveur-BD", "adresse_ip": "192.168.2.102", "type": "SERVEUR"},
      {"nom": "Client-Compta", "adresse_ip": "192.168.2.103", "type": "PC"},
      {"nom": "Client-Admin", "adresse_ip": "192.168.2.104", "type": "PC"},
  ]

Résultat attendu :
  ✓ config.py contient les 4 VMs avec leurs IPs réelles
  ✓ Tous les autres paramètres restent identiques

─────────────────────────────────────────────────────

ÉTAPE 2.4 : Ajuster les seuils de détection (optionnel)
─────────────────────────────────────────────────────

Recommandations pour un test plus rapide :
  INTERVALLE_SUPERVISION = 10     ← Au lieu de 30 (pour réagir plus vite)
  SEUIL_PANNES_CONSECUTIVES = 2   ← Au lieu de 3 (panne détectée plus vite)
  TIMEOUT_PING = 2                ← Au lieu de 1 (laisser plus de temps)

Ces paramètres accélèrent les tests mais peuvent être réajustés après.

─────────────────────────────────────────────────────

ÉTAPE 2.5 : Supprimer la base de données existante
─────────────────────────────────────────────────

Avant de redémarrer le superviseur, supprimer :
  - supervision.db (base de données SQLite existante)
  
Cela force la création d'une nouvelle base vide avec les 4 VMs.

Action sur Windows PowerShell :
  $ cd c:\Users\ANIA\Desktop\Programmation\Python\MyprojectCv.py\LogicielSupervision
  $ del supervision.db

Résultat attendu :
  ✓ Lors du redémarrage du superviseur, une nouvelle base est créée
  ✓ Elle contient uniquement les 4 VMs réelles

================================================================================
PHASE 3 : DÉMARRER LE SYSTÈME DE SUPERVISION
================================================================================

ÉTAPE 3.1 : Lancer le superviseur en arrière-plan
───────────────────────────────────────────────

Dans une console PowerShell ou Cmd :
  $ cd c:\Users\ANIA\Desktop\Programmation\Python\MyprojectCv.py\LogicielSupervision
  $ python superviseur.py

Résultat attendu :
  ==================================================
    SYSTÈME DE SUPERVISION RÉSEAU
    Démarrage...
  ==================================================
  [SUPERVISEUR] Initialisation des équipements...
    ✓ Serveur-Web (192.168.2.101) enregistré
    ✓ Serveur-BD (192.168.2.102) enregistré
    ✓ Client-Compta (192.168.2.103) enregistré
    ✓ Client-Admin (192.168.2.104) enregistré
  [SUPERVISEUR] Initialisation terminée.
  
  ==================================================
  [CYCLE] HH:MM:SS - supervision de 4 équipements
  ==================================================
    [OK] Serveur-Web (192.168.2.101) - latence : 1.2 ms
    [OK] Serveur-BD (192.168.2.102) - latence : 0.8 ms
    [OK] Client-Compta (192.168.2.103) - latence : 1.5 ms
    [OK] Client-Admin (192.168.2.104) - latence : 1.0 ms

⚠️ Le superviseur va continuer à tourner et pinger les 4 VMs toutes les 10 secondes.

─────────────────────────────────────────────────────

ÉTAPE 3.2 : Lancer l'interface web (dans une autre console)
─────────────────────────────────────────────────────────

Ouvrir une nouvelle console PowerShell / Cmd :
  $ cd c:\Users\ANIA\Desktop\Programmation\Python\MyprojectCv.py\LogicielSupervision
  $ python appli.py

Résultat attendu :
  * Running on http://localhost:5000
  * Press CTRL+C to quit

Depuis votre navigateur (Firefox, Chrome, Edge) :
  → Aller à http://localhost:5000
  
Dashboard attendu :
  ✓ Liste des 4 VMs
  ✓ Statut [OK] en vert pour chaque VM (car elles pinguent bien)
  ✓ Latence affichée en ms

Identifiants :
  Email : admin@localhost
  Mot de passe : admin

================================================================================
PHASE 4 : TESTER LA DÉTECTION DE PANNES
================================================================================

ÉTAPE 4.1 : Arrêter une VM pour simuler une panne réseau
──────────────────────────────────────────────────────

Depuis VMware Workstation :
  1. Sélectionner une VM (par exemple VM2 - Serveur-BD)
  2. Clic-droit → Power → Suspend (suspend la VM)
     OU clic sur le bouton "Suspend" dans VMware

Observation en temps réel :
  ✓ Dans la console du superviseur : vous allez voir
    [ECHEC] Serveur-BD (192.168.2.102) - échec 1/2
    [ECHEC] Serveur-BD (192.168.2.102) - échec 2/2
    [ALERTE] Serveur-BD (192.168.2.102) - PANNE DÉTECTÉE
  
  ✓ Dans le dashboard web (http://localhost:5000) :
    - Le statut de Serveur-BD passe au rouge [DOWN]
    - Une alerte s'ajoute à la section "Alertes actives"

Résultat attendu : La panne est détectée et signalée en ≤ 20 secondes

─────────────────────────────────────────────────────

ÉTAPE 4.2 : Redémarrer la VM pour simuler une récupération
──────────────────────────────────────────────────────

Depuis VMware Workstation :
  1. Clic-droit sur VM2 → Power → Resume
     OU clic sur le bouton "Resume"

Observation :
  ✓ Dans la console du superviseur :
    [OK] Serveur-BD (192.168.2.102) - latence : 0.9 ms
  
  ✓ Dans le dashboard web :
    - Le statut revient au vert [UP]
    - L'alerte reste active (elle ne disparaît qu'après acquittement)

─────────────────────────────────────────────────────

ÉTAPE 4.3 : Acquitter l'alerte depuis le dashboard
──────────────────────────────────────────────────

Dans le dashboard (http://localhost:5000) :
  1. Clic sur "Alertes" en haut
  2. Clic sur le bouton "Acquitter" en face de l'alerte Serveur-BD

Résultat :
  ✓ L'alerte disparaît de la liste (elle est marquée comme acquittée)
  ✓ Historique conservé dans la base de données

─────────────────────────────────────────────────────

ÉTAPE 4.4 : Tester les défaillances multiples
──────────────────────────────────────────────

Pour un test plus complet, simuler plusieurs scénarios :
  
  Scénario 1 : Arrêter VM1 (Serveur-Web)
    → Vérifier panne détectée en < 20 secondes
    → Redémarrer et acquitter
  
  Scénario 2 : Arrêter VM3 (Client-Compta)
    → Vérifier panne détectée
    → Laisser arrêtée pendant 2-3 minutes
    → Redémarrer et observer le temps de récupération
  
  Scénario 3 : Arrêter VM1 et VM4 simultanément
    → Vérifier que DEUX alertes sont créées
    → Redémarrer progressivement et observer

Résultat attendu :
  ✓ Toutes les pannes sont détectées
  ✓ Les alertes s'affichent correctement
  ✓ La récupération est bien détectée
  ✓ Les alertes peuvent être acquittées

================================================================================
PHASE 5 : VALIDATION ET OPTIMISATION
================================================================================

ÉTAPE 5.1 : Vérifier les métriques dans la base de données
──────────────────────────────────────────────────────────

Optionnel (pour vérifier les données brutes) :
  $ sqlite3 supervision.db
  
  > SELECT equipement_id, timestamp, statut, latence FROM metriques LIMIT 20;
  
Cela affiche les 20 dernières métriques enregistrées.

─────────────────────────────────────────────────────

ÉTAPE 5.2 : Consulter les alertes dans la base
──────────────────────────────────────────────

Depuis SQLite :
  > SELECT id, equipement_id, niveau, date_creation, acquittee FROM alertes;
  
Cela affiche toutes les alertes (y compris celles acquittées).

─────────────────────────────────────────────────────

ÉTAPE 5.3 : Optimiser les seuils en fonction des résultats
───────────────────────────────────────────────────────

Si la détection est trop lente :
  → Diminuer INTERVALLE_SUPERVISION (ex: 5 au lieu de 10)
  → Diminuer SEUIL_PANNES_CONSECUTIVES (ex: 1 au lieu de 2)

Si la détection est trop rapide (faux positifs) :
  → Augmenter TIMEOUT_PING
  → Augmenter SEUIL_PANNES_CONSECUTIVES

Formule de temps de détection :
  Temps = INTERVALLE_SUPERVISION × SEUIL_PANNES_CONSECUTIVES
  
  Exemple : 10 secondes × 2 échechs = 20 secondes avant alerte

─────────────────────────────────────────────────────

ÉTAPE 5.4 : Tests de charge (optionnel)
────────────────────────────────────────

Pour tester la stabilité du système :
  1. Garder le superviseur actif pendant 30 minutes
  2. Arrêter/Redémarrer des VMs au hasard
  3. Vérifier qu'aucun bug n'apparaît
  4. Vérifier que la base de données ne se corrompt pas
  5. Vérifier que le CPU/RAM restent stables

Résultat attendu :
  ✓ Pas de crash
  ✓ Pas d'erreurs Python
  ✓ Pas de perte de données

================================================================================
RÉSUMÉ RAPIDE (CHECKLIST)
================================================================================

Phase 1 - Infrastructure réseau :
  [ ] 4 VMs créées dans VMware avec installation Ubuntu Server minimale
  [ ] Mode Bridged configuré sur chaque VM
  [ ] PC hôte connecté au routeur physique via Ethernet
  [ ] IPs statiques assignées (192.168.2.101-104 sur les VMs)
  [ ] Pings depuis la machine hôte vers les VMs réussissent

Phase 2 - Logiciel (sur PC Windows) :
  [ ] Flask installé sur le PC hôte (pip install flask)
  [ ] config.py mis à jour avec les vraies IPs des VMs
  [ ] supervision.db supprimé (pour réinitialiser la base)
  [ ] Seuils ajustés si besoin (INTERVALLE_SUPERVISION, etc.)

Phase 3 - Démarrage :
  [ ] Superviseur lancé avec python superviseur.py
  [ ] Tous les équipements (4 VMs) sont détectés et enregistrés
  [ ] Interface web accessible sur http://localhost:5000
  [ ] Dashboard affiche les 4 VMs en [OK] avec latence

Phase 4 - Tests de détection de pannes :
  [ ] Arrêt d'une VM (Power Off dans VMware) → panne détectée
  [ ] Console superviseur affiche "[ALERTE]" après ~20 secondes
  [ ] Dashboard web affiche la VM en rouge [DOWN]
  [ ] Redémarrage de la VM → statut revient au vert [UP]
  [ ] Alerte acquittée depuis le dashboard → elle disparaît
  [ ] Tests multiples avec différentes VMs réussis

Phase 5 - Validation :
  [ ] Métriques enregistrées correctement dans la base (SELECT * FROM metriques)
  [ ] Alertes créées et acquittées (SELECT * FROM alertes)
  [ ] Aucun crash du superviseur pendant 30+ minutes de test
  [ ] Seuils optimisés selon vos besoins réels

================================================================================
TRUCS & ASTUCES
================================================================================

💡 Raccourcis utiles :

  Pour arrêter le superviseur :
    → CTRL+C dans la console PowerShell

  Pour redémarrer avec une base vierge :
    → Supprimer supervision.db
    → Redémarrer le superviseur

  Pour voir les logs détaillés :
    → Les logs sont affichés en temps réel dans la console du superviseur

  Pour déboguer une VM qui ne répond pas :
    → Depuis la VM : $ ping -c 1 192.168.2.1 (votre passerelle)
    → Depuis l'hôte : $ ping 192.168.2.XXX

  Pour obtenir l'IP d'une VM :
    → Depuis la VM : $ ip addr show | grep "192.168"

💡 Points importants sur le mode Bridged :

  Avantages :
    ✓ Les VMs obtiennent des IPs réelles du routeur (pas de NAT)
    ✓ Pas de configuration réseau complexe dans VMware
    ✓ Les VMs sont sur le même réseau que la machine hôte
    ✓ La simulation est très réaliste
  
  Attention :
    ✓ Ne déconnectez PAS l'adaptateur réseau physique du routeur
    ✓ Les VMs utiliseront la même interface réseau que votre PC
    ✓ Si vous perdez la connexion au routeur, les VMs aussi
    ✓ Toutes les VMs doivent être configurées avec le MÊME adaptateur réseau Bridged

💡 Si vous ne voyez pas les IPs en mode Bridged :

  1. Vérifier que VMware "Virtual Network Editor" montre l'adaptateur bridgé activé
  2. Redémarrer la VM (parfois necessite un redémarrage pour obtenir l'IP du routeur)
  3. Vérifier que le routeur DHCP fonctionne correctement
  4. Vérifier que l'adaptateur physique du PC est bien connecté au routeur

💡 Changements après les tests :

  Pour revenir à l'ancienne configuration fictive :
    1. Restaurer config_BACKUP.py → config.py
    2. Supprimer supervision.db
    3. Redémarrer le superviseur

  Pour tester avec une autre approche réseau :
    - Vous pouvez toujours basculer vers un réseau virtuel VMware
    - Ou utiliser plusieurs routeurs physiques
    - Ou combiner les deux (certaines VMs bridgées, d'autres virtuelles)

================================================================================
CONCLUSION
================================================================================

Ce plan vous permet de :
  ✓ Tester le système de supervision sur des VMs réelles en mode Bridged
  ✓ Utiliser votre routeur physique pour la gestion du réseau
  ✓ Valider que la détection de pannes fonctionne correctement
  ✓ Vérifier que les alertes s'affichent bien
  ✓ Optimiser les seuils en fonction de vos besoins
  ✓ Obtenir une simulation très réaliste d'un réseau d'entreprise

Éléments clés :
  ✓ Aucun installation Python sur les VMs requise
  ✓ Le logiciel tourne 100% sur votre PC Windows
  ✓ Les VMs réagissent simplement au ping (automatique)
  ✓ Configuration simple et directe sans réseau virtuel VMware complexe
  ✓ Très réaliste : les VMs utilisant des vraies adresses du routeur

Durée estimée pour tout le plan : 2-3 heures
  - Création et configuration des VMs : 45 min - 1h
  - Configuration mode Bridged et IPs : 15 min
  - Adaptation du logiciel : 10 min
  - Tests de fonctionnement : 30 min
  - Optimisation et troubleshooting : 30-60 min

Notes finales :
  → Gardez le routeur toujours actif pendant les tests
  → Évitez de débrancher le câble réseau de votre PC pendant les tests
  → Les VMs peuvent rester démarrées en permanence si besoin
  → Le supervisor peut tourner 24h/24 en arrière-plan

Bonne chance ! 🚀