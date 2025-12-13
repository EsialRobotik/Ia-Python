# Ia-Python

Python IA for EsialRobotik's Princesses

## Makefile
Prérequis : créer un fichier `.env.ROBOT` en clonant `.env.ROBOT.dist` et en mettant les valeurs appropriées des différentes variables d'environnement.
Les `ROBOT` sont `princess`, `pami0`, `pami1`, etc.
`Makefile deploy-ROBOT` permet ensuite de copier l'IA sur le robot

## Configurer votre PYTHONPATH
Pour que les imports fonctionnent correctement, il faut ajouter le dossier `.` à votre PYTHONPATH.
Pour cela, ajoutez la ligne suivante à votre `.bashrc` ou `.zshrc` :
```
export PYTHONPATH=$PYTHONPATH:.
```
Pour modifier temporairement votre PYTHONPATH, vous pouvez exécuter la commande suivante :
```
export PYTHONPATH=$PYTHONPATH:.
``` 
Sous windows, vous devez créer ou modifier une variable d'environnement `PYTHONPATH` avec la valeur `.`.


### Année
L'année doit avoir son répertoire dans `config`

### Robot
Le robot doit avoir son répertoire dans `config/{annee}/` et exister dans l'enum `Robot` dans `ia/utils/robot.py`

### Log level
Les niveaux de log disponibles sont :
- `DEBUG`'
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

## Lancer l'IA
```
python ia/main.py {annee} {robot} {log_level}
```

## Divers
Source du pathfinding LUA : https://github.com/GlorifiedPig/Luafinding/tree/master