# CLAUDE.md

Ce fichier fournit des indications à Claude Code (claude.ai/code) pour travailler dans ce dépôt.

## Présentation du projet

**Ia-Python** est un framework d'autonomie robotique modulaire et piloté par la configuration, destiné à la Coupe de 
France de Robotique. Il tourne sur Raspberry Pi et contrôle les robots via une architecture en couches : managers, 
APIs matérielles, pathfinding et exécution d'actions.

Robots supportés : `princess` (principal), `pami0`–`pami4` (robots secondaires).

## Commandes

**Installation :**
```bash
python3 -m venv --system-site-packages env
source env/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:.   # À ajouter aussi dans ~/.bashrc
```

**Lancer l'IA (mode match) :**
```bash
python ia/main.py {année} {robot} {log_level}
# Exemple : python ia/main.py 2025 princess DEBUG
```

**Tester un composant individuel :**
```bash
python ia/test.py {mode} {année} {robot} {log_level}
# Modes : chrono, pullcord, color, nextion, log_socket, com_socket, ax12,
#         srf04, srf08, lidar, asserv, actions, pathfinding, strategy
```

**Déployer sur un robot :**
```bash
make deploy-princess   # ou deploy-pami0 à deploy-pami4
# Nécessite les fichiers .env.{robot} (copier .env.dist et remplir les credentials SSH)
```

## Architecture

### Structure en couches

```
main.py / test.py
    └── MasterLoop (ia/master_loop.py)
            ├── StrategyManager    – choisit le prochain objectif depuis strategy.json
            ├── MovementManager    – transmet les commandes de déplacement vers l'Asserv
            ├── ActionManager      – exécute les séquences d'actions
            ├── DetectionManager   – lit les capteurs, met à jour la carte d'obstacles
            ├── Asserv (ia/asservissement/) – communication série avec la carte moteur
            ├── Pathfinding (ia/pathfinding/) – A* en Lua via lupa
            └── APIs (ia/api/)  – GPIO, capteurs, périphériques série
```

### Système de configuration

Tout le comportement du robot est piloté par la config. Chaque combinaison robot/année possède :
- `config/{année}/{robot}/config.json` – Pins matérielles, ports série, valeurs PID, géométrie de table, seuils de détection
- `config/{année}/{robot}/strategy.json` – Objectifs du match avec deux branches (`color0` / `color3000`), positions, listes d'actions, valeurs en points
- `config/{année}/{robot}/actions/` – Définitions JSON des actions individuelles

Le répertoire `strategy/` contient un DSL Python qui génère les fichiers `strategy.json` — modifier les scripts Python 
puis les exécuter pour régénérer le strategy.json.

### Modules clés

| Module | Rôle |
|--------|------|
| `ia/manager/` | Orchestrateurs haut niveau (Strategy, Movement, Action, Detection, Communication) |
| `ia/asservissement/asserv.py` | Communication série thread-safe avec le contrôleur moteur ; go/turn/goto/odométrie |
| `ia/pathfinding/astar.py` | Pathfinding A* via runtime Lua (lupa) + Shapely pour la géométrie des obstacles |
| `ia/actions/` | Framework d'actions : base abstraite, repository/factory, actions concrètes |
| `ia/api/` | Drivers matériels : servos AX-12, lidar, ultrason (SRF04/08), GPIO, sockets |
| `server/` | Serveur tournant sur une Raspberry Pi dédiée : agrège les logs de tous les robots et sert de relais de communication inter-robots |
| `simulator/` | Outil graphique (PySide6) pour simuler les stratégies, tester les déplacements et rejouer des matchs à partir des logs |
| `utils/` | Utilitaires divers ; contient actuellement une interface Textual pour contrôler l'asserv manuellement |
| `strategy/` | DSL Python pour générer strategy.json ; stratégies annuelles dans `strategy/main/` |

### Framework d'actions

Les actions héritent de `ia/actions/abstract_action.py` et implémentent `execute()`, `finished()`, `stop()`, `reset()`,
`get_flag()`. L'`ActionRepositoryFactory` instancie les actions depuis la config JSON. Types d'actions : servo PWM, 
séquences AX-12, actionneurs GPIO, attentes.

### Déroulement d'un match

1. Chargement de la config pour l'année+robot → initialisation de tous les managers et du matériel
2. Attente du cordon de départ → démarrage du chrono (match de 89s)
3. L'écran Nextion exécute la séquence de calibration
4. Boucle principale : récupérer l'objectif → chemin A* → MovementManager enfile les mouvements → ActionManager 
5. exécute les actions → DetectionManager met à jour les obstacles → répéter jusqu'à la fin du chrono

### Messages CBOR

L'asservissement utilise la sérialisation CBOR2 pour les messages série (voir `ia/asservissement/` pour les définitions des messages).