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

