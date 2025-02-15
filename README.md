# Ia-Python

Python IA for EsialRobotik's Princesses

## Makefile
Prérequis : créer un fichier `.env.local` en conant `.env.local.dist` et en mettant les valeurs appropriées des différentes variables d'environnement.
`Makefile deploy` permet ensuite de copier l'IA sur le robot

## Configurer votre PYTHONPATH
Pour que les imports fonctionnent correctement, il faut ajouter le dossier `.` à votre PYTHONPATH.
Pour cela, ajoutez la ligne suivante à votre `.bashrc` ou `.zshrc` :
```
PYTHONPATH=$PYTHONPATH:.
```
Pour modifier temporairement votre PYTHONPATH, vous pouvez exécuter la commande suivante :
```
export PYTHONPATH=$PYTHONPATH:.
``` 
Sous windows, vous devez créer ou modifier une variable d'environnement `PYTHONPATH` avec la valeur `.`.

## Virtual env
- Create a virtual env [VSCode Venv](https://code.visualstudio.com/docs/python/environments) or the following command in the directory
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
```
pip install -r requirements.txt
```

## Génération de la table de jeu
### Préparer la configuration
Dans le fichier `config.json`, configurer la table et les zones interdites dans la clé `table`.
### Générer les fichiers tbl
```
python ia/pathfinding/Table.py YEAR
```