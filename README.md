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

