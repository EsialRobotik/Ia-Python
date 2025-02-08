# Ia-Python

Python IA for EsialRobotik's Princesses

## Makefile
Prérequis : créer un fichier `.env.local` en conant `.env.local.dist` et en mettant les valeurs appropriées des différentes variables d'environnement.
`Makefile deploy` permet ensuite de copier l'IA sur le robot

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