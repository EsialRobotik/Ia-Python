# Introduction

Le projet `Ia-Python` héberge l'intelligence artificielle (IA) développée en Python par l'équipe EsialRobotik pour la Coupe de France de Robotique. Conçue pour s'exécuter sur un Raspberry Pi embarqué, cette IA a pour mission de piloter l'intégralité du robot pendant un match, de la prise de décision stratégique à l'exécution des mouvements et actions.

Grâce à son système de configuration, cette même base de code est capable de piloter aussi bien le robot principal que les robots secondaires (les "Pamis"), chacun ayant ses propres spécificités matérielles et stratégiques.

## Philosophie du Projet

L'architecture du projet repose sur trois principes fondamentaux pour assurer sa flexibilité, sa robustesse et sa maintenabilité au fil des années :

*   **Approche Modulaire** : Le code est structuré en modules indépendants et spécialisés (managers, actions, API matérielle, etc.). Cette séparation claire des responsabilités simplifie le développement, le débogage et les tests de chaque composant. Elle permet surtout d'étendre facilement les capacités du robot en ajoutant de nouvelles fonctionnalités sans risquer de perturber le système existant.

*   **Pilotage par la Configuration** : Le comportement du robot (séquences d'actions, stratégies, paramètres techniques) n'est pas inscrit dans le code, mais défini dans des fichiers de configuration au format JSON. Cette externalisation permet d'adapter ou de modifier une stratégie, d'ajuster un paramètre ou de configurer un nouveau robot en modifiant simplement un fichier texte, sans toucher au code source de l'IA.

*   **Orientation Tests** : Le projet intègre un puissant script de test (`ia/test.py`) qui permet de valider chaque module de manière unitaire et indépendante. De la communication avec un servomoteur à la validation d'une stratégie complète, ces tests sont essentiels pour garantir la fiabilité de chaque brique logicielle avant de l'intégrer sur le robot.

## Architecture Générale

L'organisation du projet est pensée pour séparer clairement les différentes responsabilités logicielles. Chaque répertoire à la racine a un rôle bien défini.

*   **Le Cœur de l'IA (`ia/`)**
    Le répertoire `ia/` contient toute la logique de l'intelligence artificielle qui s'exécute sur le Raspberry Pi du robot. C'est le cerveau du robot, responsable de la prise de décision, de la gestion des mouvements et de l'exécution des actions pendant un match.

*   **La Configuration (`config/`)**
    Ce répertoire est la clé de la flexibilité du projet. Il contient des fichiers de configuration au format JSON qui décrivent le comportement du robot, ses actions, ses stratégies et ses paramètres techniques. L'arborescence suit une logique `config/ANNEE/ROBOT/` (par exemple, `config/2025/princess/`), ce qui permet d'adapter l'IA aux spécificités du règlement de l'année et aux caractéristiques matérielles de chaque robot, sans jamais modifier le code source.

*   **Le Serveur de Communication (`server/`)**
    Le répertoire `server/` contient un serveur dont le rôle est multiple : il permet aux différents robots d'échanger des informations entre eux, centralise les logs de chaque machine pour éviter les problèmes de synchronisation et permet à un simulateur de suivre en temps réel l'état des robots.

*   **La Définition de Stratégie (`strategy/`)**
    Ce répertoire contient le code qui permet de décrire de manière simple les objectifs du robot (positions à atteindre, séquences d'actions, calcul des points). Ce code abstrait ensuite cette logique pour générer les fichiers de stratégie au format JSON qui seront utilisés par l'IA.

*   **Les Tests (`ia/test.py`)**
    Le fichier `ia/test.py` est un script de test polyvalent qui permet de valider unitairement et indépendamment chaque composant matériel ou logiciel du robot. De la vérification d'un servomoteur au test d'une séquence d'actions complexe, ce script est fondamental pour assurer la fiabilité du robot avant un match.

# Architecture du Cœur de l'IA

Le répertoire `ia/` est le véritable cerveau du robot. Il contient toute la logique qui s'exécute sur le Raspberry Pi embarqué et qui est responsable de l'autonomie du robot pendant un match. Son architecture est conçue pour être modulaire, chaque sous-répertoire ayant une responsabilité claire.

## Les `Managers` (`ia/manager/`)
Les managers sont les chefs d'orchestre de l'IA. Chaque manager est spécialisé dans une tâche de haut niveau :
* `StrategyManager` : Interprète la stratégie en cours et décide du prochain objectif à atteindre.
* `MovementManager` : Gère les déplacements du robot en faisant appel à l'asservissement et au pathfinding.
* `ActionManager` : Exécute les séquences d'actions complexes (manipulation d'objets, activation d'actuateurs).
* `DetectionManager` : Gère les informations provenant des capteurs de détection d'obstacles.

## Les `Actions` (`ia/actions/`)
Ce répertoire définit toutes les actions atomiques que le robot peut réaliser. Une action peut être aussi simple que "attendre une seconde" (`action_wait.py`) ou plus complexe comme "actionner un servomoteur". Ces actions sont ensuite assemblées par le `ActionManager` pour réaliser les objectifs définis dans la stratégie.

## L'`API` Matérielle (`ia/api/`)
L'API est la couche de communication de bas niveau qui fait le pont entre le code de l'IA et les composants matériels du robot. Chaque module de ce répertoire est dédié à un périphérique spécifique : communication avec les servomoteurs AX-12, lecture de la tirette de démarrage, gestion de l'afficheur, etc. Cette abstraction permet au reste du code de manipuler le matériel sans se soucier des détails d'implémentation du protocole de communication.

## L'Asservissement et le `Pathfinding` (`ia/asservissement/` et `ia/pathfinding/`)
Ces deux répertoires sont au cœur du contrôle des mouvements du robot.
* `asservissement` : Contient la logique de contrôle en boucle fermée de la position et de l'orientation du robot. Il reçoit des consignes de déplacement (avancer, tourner) et les traduit en commandes pour les moteurs des roues.
* `pathfinding` : Calcule la trajectoire optimale pour que le robot atteigne une destination en évitant les obstacles (autres robots, éléments de jeu). Le projet utilise notamment un algorithme A* pour cette tâche.

# Lancement et Tests

Cette section décrit comment lancer l'intelligence artificielle en conditions de match et comment utiliser le script de test pour valider les différents composants du robot.

## Lancer l'IA en mode match

Le point d'entrée pour démarrer le robot en mode match est le script `ia/main.py`. Il initialise tous les managers, charge la configuration et la stratégie, puis démarre la boucle principale de l'IA.

La commande pour lancer l'IA est la suivante :
```bash
python ia/main.py {annee} {robot} {log_level}
```
* {annee} : L'année de la coupe (ex: 2025), qui doit correspondre à un répertoire dans config/.
* {robot} : Le nom du robot (ex: princess), qui doit avoir une configuration définie pour l'année choisie.
* {log_level} : Le niveau de verbosité des logs (ex: INFO, DEBUG).

## Utiliser le script de test (ia/test.py)

Le script ia/test.py est un outil essentiel pour le débogage. Il permet de tester de manière isolée chaque module logiciel ou matériel, sans avoir à lancer l'intégralité de l'IA.

La commande pour utiliser le script de test est :
```bash
python ia/test.py {mode} {annee} {robot} {log_level}
```

Le paramètre {mode} spécifie le composant à tester. Voici quelques-uns des modes disponibles, la liste exhaustive se trouve dans la classe et le README :
* ax12 : Pour tester les servomoteurs.
* asserv : Pour valider le bon fonctionnement de l'asservissement.
* pathfinding : Pour tester l'algorithme de recherche de chemin.
* actions : Pour lancer une séquence d'actions spécifique depuis la console.
* strategy : Pour vérifier le déroulement d'une stratégie sans interaction matérielle.
* pullcord, color, lidar : Pour tester les capteurs et périphériques correspondants.

Les autres paramètres (annee, robot, log_level) sont identiques à ceux du lancement en mode match.

# Configuration, Communication et Stratégie

Au-delà du cœur de l'IA, plusieurs composants clés permettent la flexibilité, la supervision et la définition du comportement du robot.

## Le Système de Configuration (`config/`)

Le répertoire `config/` est fondamental pour l'adaptabilité du projet. Il externalise tous les paramètres variables dans des fichiers JSON, ce qui permet de modifier le comportement du robot sans toucher au code source. L'organisation `config/ANNEE/ROBOT/` (ex: `config/2025/princess/`) assure que chaque robot possède une configuration adaptée aux règles de l'année et à ses spécificités matérielles.

On y trouve notamment :
* Les paramètres de l'asservissement (valeurs PID, dimensions du robot).
* Les définitions des séquences d'actions.
* Les stratégies de match.
* Le mapping des broches (pins) pour les capteurs et actuateurs.

## Le Serveur de Communication (`server/`)

Le script `server/Server.py` lance un serveur indépendant qui joue un rôle central dans l'écosystème multi-robots. Ses responsabilités sont :
*   **Communication inter-robot** : Permettre aux robots d'échanger des informations stratégiques, comme la position ou les objectifs déjà réalisés.
*   **Centralisation des logs** : Agréger les logs de tous les robots en un seul flux pour faciliter le débogage et l'analyse post-match.
*   **Interface pour simulateur** : Fournir un point d'accès pour qu'un simulateur puisse suivre en temps réel l'état et les actions des robots.

## La Définition de Stratégie (`strategy/`)

Ce répertoire contient un ensemble de scripts Python conçus pour simplifier la création de stratégies de match. Plutôt que d'écrire manuellement des fichiers JSON complexes, le développeur utilise ces scripts pour décrire les objectifs à un plus haut niveau (ex: "aller à la position X,Y", "exécuter la séquence d'actions 'prendre_gobelet'", "marquer 10 points").

L'exécution de ces scripts génère ensuite les fichiers de stratégie au format JSON, qui sont placés dans le répertoire de configuration (`config/`) pour être lus par le `StrategyManager` de l'IA.

# Déploiement Simplifié avec `Makefile` et `.env`

Pour faciliter le déploiement du code sur les robots, le projet utilise un `Makefile` qui automatise l'exécution de scripts de déploiement. La configuration de l'environnement, notamment les informations de connexion aux robots, est gérée via des fichiers d'environnement.

## Cibles de Déploiement du `Makefile`

Le `Makefile` fournit des commandes directes pour déployer le code sur un robot spécifique. Ces commandes se chargent d'exécuter les scripts nécessaires pour la synchronisation du code.

*   `make deploy-princess` : Lance le script de déploiement pour le robot "princess".
*   `make deploy-pami0` : Lance le script de déploiement pour le robot "pami0".

## Gestion de la Configuration avec les Fichiers `.env`

Chaque commande de déploiement exécute d'abord un script `check_load_env.sh`. Ce script est responsable du chargement des variables d'environnement nécessaires au déploiement, telles que l'adresse IP du robot ou les identifiants de connexion.

Cette approche permet de stocker les informations sensibles et spécifiques à chaque environnement (par exemple, dans des fichiers `.env.princess` ou `.env.pami0`) en dehors des scripts de déploiement. Ainsi, pour déployer le code, il suffit de s'assurer que le fichier d'environnement correspondant au robot cible est correctement configuré avant de lancer la commande `make` appropriée.
