# Ia-Python

Python IA for EsialRobotik's Princesses

## Makefile
Prérequis : créer un fichier `.env.local` en conant `.env.local.dist` et en mettant les valeurs appropriées des différentes variables d'environnement.
`Makefile deploy` permet ensuite de copier l'IA sur le robot

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

## Virtual env
En local, il est recommandé d'utiliser un environnement virtuel pour installer les dépendances du projet.
- Créer virtual env [VSCode Venv](https://code.visualstudio.com/docs/python/environments) ou en ligne de commande :
```
python -m venv env  
```
- Activate the environment
#### Windows
```
.\env\Scripts\activate.bat
```
#### Linux
```
source env/bin/activate
```

## Install required modules
### Local
```
pip install -r requirements.txt
```
### Robot
```
sudo apt-get install python3-gpiozero python3-smbus2 python3-numpy python3-shapely python3-networkx python3-lupa
```

## Lancer les tests
```
python ia/test.py {mode} {annee} {log_level}
```
### Les modes
Les modes disponibles sont :
- chrono : Test le chrono
- pullcord : Test la tirette
- color : Test le sélecteur de couleur
- nextion : Test l'écran Nextion
- log_socket : Test la connexion au socket de log
- com_socket : Test la connexion au socket de communication
- ax12 : Test les servomoteurs AX-12
- srf04 : Test les capteurs à ultrasons SRF04
- lidar : Test le lidar
- asserv : Test l'asservissement
- actions : Test les actions, permet de lancer des actions via la console
- pathfinding : Test le pathfinding
- strategy : Test le strategy_manager

### Année
L'année doit avoir son répertoire dans `config`

### Log level
Les niveaux de log disponibles sont :
- `DEBUG`'
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

## Lancer l'IA
```
python ia/main.py {annee} {log_level}
```