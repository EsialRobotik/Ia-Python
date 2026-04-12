# Systeme d'actions

Ce package gere l'execution d'actions sur le robot (servomoteurs, actionneurs serie, attentes, etc.).
Les actions sont declarees dans des fichiers JSON et instanciees automatiquement au demarrage.

## Architecture

```
ia/actions/
├── abstract_action.py          # Interface de base (5 methodes abstraites)
├── threaded_action.py          # Classe de base pour les actions asynchrones (thread)
├── registry.py                 # Registre @action_type pour l'auto-enregistrement
├── serial_port.py              # Wrapper pyserial pour les actionneurs serie
├── action_repository.py        # Stockage cle/valeur des actions instanciees
├── action_repository_factory.py  # Charge les JSON et instancie les actions
└── types/                      # Un fichier par type d'action
    ├── action_wait.py          # type: "wait"
    ├── action_list.py          # type: "list"
    ├── action_ax12.py          # type: "AX12"
    ├── action_actuator.py      # type: "actuator"
    └── action_pwm_servo.py     # type: "pwm_servo"
```

## Fonctionnement

### Cycle de vie d'une action

Chaque action implemente 5 methodes definies dans `AbstractAction` :

1. **`execute()`** - Lance l'action (non-bloquant). Ne relance pas une action deja terminee sans `reset()`.
2. **`finished()`** - Retourne `True` quand l'action est terminee.
3. **`stop()`** - Arrete immediatement l'action.
4. **`reset()`** - Reinitialise l'action pour pouvoir la relancer.
5. **`get_flag()`** - Retourne un flag optionnel qui influence les decisions de la strategie.

### Auto-enregistrement

Chaque type d'action se declare via le decorateur `@action_type("nom")` :

```python
from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction

@action_type("mon_type")
class MonAction(ThreadedAction):
    ...
```

Au chargement du module, la classe est enregistree dans le dictionnaire `ACTION_TYPES`.
La factory (`action_repository_factory.py`) consulte ce dictionnaire pour instancier
les actions depuis les fichiers JSON, sans avoir besoin de `match/case` centralisee.

### ThreadedAction

La majorite des actions executent du travail dans un thread daemon.
`ThreadedAction` factorise ce pattern : il suffit d'implementer `_run()`.

```python
class MonAction(ThreadedAction):
    def _run(self):
        # Faire le travail ici
        # Verifier self._stop_requested pour un arret propre
        self._finished = True
```

Les methodes `execute()`, `finished()`, `stop()`, `reset()` et `get_flag()`
sont deja implementees par `ThreadedAction`.

Pour les actions synchrones (ex: AX12 qui ne necessite pas de thread), heriter
directement de `AbstractAction`.

## Configuration JSON

Chaque action est un fichier JSON dans `config/{annee}/{robot}/actions/`.
Le nom du fichier (sans `.json`) devient l'identifiant de l'action.

### Structure commune

```json
{
    "type": "<type enregistre via @action_type>",
    "description": "Description lisible",
    "alias": "raccourci_optionnel",
    "payload": {
        // parametres specifiques au type
    }
}
```

### Types disponibles

#### wait - Attente

```json
{
    "type": "wait",
    "alias": "W",
    "payload": {
        "duration": 1.5
    }
}
```

#### AX12 - Servo Dynamixel

```json
{
    "type": "AX12",
    "alias": "ateh",
    "payload": {
        "type": "position",
        "id": 13,
        "angleDegree": 300
    }
}
```

Sous-types disponibles dans `payload.type` :
- `position` - avec `angleDegree` (0-300) ou `angleRaw` (0-1023)
- `disableTorque` - desactive le couple
- `complianceSlope` - regle la souplesse (champ `value`)
- `complianceMargin` - regle la marge de compliance (champ `value`)

#### list - Sequence d'actions

```json
{
    "type": "list",
    "alias": "pil",
    "payload": {
        "list": [
            "pince_int_gauche_lacher",
            "pince_int_droite_lacher"
        ]
    }
}
```

Execute les actions referencees une par une dans l'ordre.
Les identifiants doivent correspondre a des actions presentes dans le repository.

#### actuator - Commandes serie

```json
{
    "type": "actuator",
    "payload": {
        "actuatorLink": "pompes",
        "commands": [
            {"command": "pump_on", "async": false, "timeout": 1.0},
            {"command": "pump_off", "async": true}
        ]
    }
}
```

- `actuatorLink` : identifiant du port serie declare dans `config.json` sous `actions.actuators`
- `async: true` : envoie la commande sans attendre de reponse
- `async: false` (defaut) : attend une reponse "ok"

#### pwm_servo - Servo PWM GPIO

```json
{
    "type": "pwm_servo",
    "alias": "O",
    "payload": {
        "gpio": 18,
        "loop": true,
        "angles": [-60, 15]
    }
}
```

- `loop: true` : repete la sequence indefiniment (l'action est consideree terminee immediatement)
- `loop: false` : execute la sequence une fois

## Tester les actions

```bash
python ia/test.py actions {annee} {robot} DEBUG
# Exemple :
python ia/test.py actions 2025 princess DEBUG
```

Cela charge toutes les actions JSON du robot et ouvre un prompt interactif.
Tapez l'identifiant d'une action (nom du fichier sans `.json`) ou son alias pour l'executer.

Exemples dans le prompt :
```
Action: ascenseur_tout_en_haut
Action: ateh
Action: pinces_lacher
```

## Ajouter un nouveau type d'action

Il suffit de creer un seul fichier dans `ia/actions/types/` et de l'importer dans
`ia/actions/types/__init__.py`. Aucun autre fichier a modifier.

### Etape 1 : Creer le fichier

```python
# ia/actions/types/action_mon_type.py
from typing import Optional
from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction


@action_type("mon_type")
class ActionMonType(ThreadedAction):

    def __init__(self, param1, param2, flags: Optional[str] = None) -> None:
        super().__init__(flags)
        self.param1 = param1
        self.param2 = param2

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionMonType':
        """Instancie l'action depuis le payload JSON.

        deps contient les dependances injectees par la factory :
        - ax12_link : lien serie AX12 (ou None)
        - serial_ports : dict des ports serie par id
        - action_repository : le repository en cours de construction
        """
        return cls(payload["param1"], payload["param2"])

    def _run(self) -> None:
        # Travail de l'action
        # Verifier self._stop_requested regulierement pour un arret propre
        self._finished = True
```

### Etape 2 : Enregistrer l'import

Ajouter une ligne dans `ia/actions/types/__init__.py` :

```python
from ia.actions.types.action_mon_type import ActionMonType  # noqa: F401
```

### Etape 3 : Creer un fichier JSON de config

```json
{
    "type": "mon_type",
    "description": "Ma nouvelle action",
    "payload": {
        "param1": "valeur1",
        "param2": 42
    }
}
```

C'est tout. La factory detectera automatiquement le type `"mon_type"` grace au
decorateur `@action_type` et appellera `from_json()` pour instancier l'action.

### Action synchrone (sans thread)

Si l'action n'a pas besoin de thread (execution instantanee), heriter de
`AbstractAction` au lieu de `ThreadedAction` et implementer les 5 methodes :

```python
@action_type("instant")
class ActionInstant(AbstractAction):
    def __init__(self, ...):
        self._executed = False

    @classmethod
    def from_json(cls, payload, **deps):
        return cls(...)

    def execute(self):
        # action immediate
        self._executed = True

    def finished(self):
        return self._executed

    def stop(self):
        pass

    def reset(self):
        self._executed = False

    def get_flag(self):
        return None
```