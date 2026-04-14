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

C'est quoi superviseur.py et pourquoi il existe ?C'est le cerveau du système — le module principal qui orchestre tout. Il tourne en boucle infinie, appelle pinger.py pour chaque équipement, enregistre les résultats dans la base via basedonne.py, et décide si une alerte doit être créée. Il correspond exactement au Moteur de Supervision dans le diagramme de composants et à la boucle principale du diagramme de séquence (loop toutes les 30 secondes).

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
