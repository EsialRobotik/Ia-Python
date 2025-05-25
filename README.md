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