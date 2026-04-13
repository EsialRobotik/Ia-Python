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
    ├── action_wait.py                  # type: "wait"
    ├── action_list.py                  # type: "list"
    ├── action_list_join.py             # type: "list_join"
    ├── action_ax12.py                  # type: "AX12"
    ├── action_actuator.py              # type: "actuator"
    ├── action_pwm_servo.py             # type: "pwm_servo"
    ├── action_camera_init.py           # type: "camera_init"
    └── action_camera_detect_aruco.py   # type: "camera_detect_aruco"
```

## Fonctionnement

### Cycle de vie d'une action

Chaque action implemente 5 methodes definies dans `AbstractAction` :

1. **`execute()`** - Lance l'action (non-bloquant). Ne relance pas une action deja terminee sans `reset()`.
2. **`finished()`** - Retourne `True` quand l'action est terminee.
3. **`stop()`** - Arrete immediatement l'action.
4. **`reset()`** - Reinitialise l'action pour pouvoir la relancer.
5. **`get_flags()`** - Retourne une liste optionnelle de flags qui influencent les decisions de la strategie.

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

Les methodes `execute()`, `finished()`, `stop()`, `reset()` et `get_flags()`
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

#### list_join - Execution parallele

```json
{
    "type": "list_join",
    "alias": "o",
    "payload": {
        "list": [
            "ouvrir_pince_1",
            "ouvrir_pince_2",
            "ouvrir_pince_3",
            "ouvrir_pince_4"
        ]
    }
}
```

Meme payload que `list`, mais lance toutes les actions simultanement (appel non-bloquant
en rafale) puis attend que toutes soient terminees avant de se marquer comme finie.
Utile pour declencher des mouvements de servos en parallele.

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

#### camera_init - Initialisation de la camera

```json
{
    "type": "camera_init",
    "description": "Initialise la camera Raspberry Pi",
    "payload": {}
}
```

Initialise le hardware Picamera2. **Doit etre executee une seule fois au demarrage**,
sinon les actions camera suivantes resteront bloquees. Typiquement placee dans
`actions.init` de `config.json`.

Cette action necessite que la camera soit declaree dans `config.json` :

```json
"actions": {
    "camera": { "active": true },
    ...
}
```

Si la section `camera` est absente, l'instanciation de l'action echoue au demarrage.

#### camera_detect_aruco - Detection de marqueurs ArUco

Prend une photo, detecte les marqueurs ArUco presents et leve des flags selon
des regles configurables. Suppose que `camera_init` a deja ete executee.

```json
{
    "type": "camera_detect_aruco",
    "alias": "detect_nj",
    "payload": {
        "dictionary": "DICT_4X4_100",
        "markers": {
            "47": "yellow",
            "36": "blue"
        },
        "sort": "left_to_right",
        "expected_count": 4,
        "rules": [
            {
                "type": "positional_label_mismatch",
                "expected_label": "yellow",
                "flag_template": "rotateNut{index}",
                "index_start": 1
            }
        ]
    }
}
```

**Payload :**
- `dictionary` (requis) : nom du dictionnaire ArUco OpenCV. Dictionnaires supportes :
  `DICT_4X4_50`, `DICT_4X4_100`, `DICT_4X4_250`, `DICT_4X4_1000`,
  `DICT_5X5_50`, `DICT_5X5_100`, `DICT_5X5_250`, `DICT_5X5_1000`,
  `DICT_6X6_50`, `DICT_6X6_100`, `DICT_6X6_250`, `DICT_6X6_1000`.
- `markers` (requis) : table `{ "id_aruco": "label" }` associant un id de marqueur
  a un label logique. Les marqueurs detectes dont l'id n'est pas dans cette table
  sont ignores.
- `sort` (optionnel) : ordre de tri des detections. Valeurs possibles :
  `left_to_right`, `right_to_left`, `top_to_bottom`, `bottom_to_top`. Sans tri,
  l'ordre retourne par OpenCV est conserve.
- `expected_count` (optionnel) : si le nombre de marqueurs detectes ne correspond
  pas, les regles ne sont pas appliquees (un warning est logge). Utile pour
  garantir la fiabilite d'une detection.
- `rules` (optionnel) : liste de regles qui produisent des flags a partir des
  detections. Les flags leves sont exposes via `get_flags()` et aggreges par
  le `StrategyManager` a la fin de l'action.

**Regles disponibles :**

1. `positional_label_mismatch` : pour chaque detection a la position i, si
   son label n'est pas `expected_label`, leve le flag `flag_template.format(index=i + index_start)`.
   Sert a demander une correction position par position.
   - `expected_label` (requis) : label attendu a chaque position
   - `flag_template` (requis) : gabarit du flag, avec `{index}` remplace par l'index
   - `index_start` (optionnel, defaut 0) : decalage ajoute a l'index

2. `label_present` : si au moins un marqueur avec ce label est detecte, leve le flag.
   - `label` (requis) : label a chercher
   - `flag` (requis) : flag a lever

3. `label_absent` : si aucun marqueur avec ce label n'est detecte, leve le flag.
   - `label` (requis) : label a chercher
   - `flag` (requis) : flag a lever

**Exemple concret** (cas noisettes 2026) : detecter les 4 caisses, identifier
leur couleur via les marqueurs 47 (jaune) et 36 (bleu), trier gauche-a-droite,
puis lever `rotateNut1`..`rotateNut4` pour chaque caisse qui n'est pas jaune.

Le JSON ci-dessus produit exactement ce comportement. Pour la variante bleue,
changer `expected_label` en `"blue"`.

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

    def __init__(self, param1, param2, flags: Optional[list[str]] = None) -> None:
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

    def get_flags(self):
        return None
```