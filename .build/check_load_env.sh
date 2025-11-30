# Script qui vérifie la présence des fichiers de config

if [ -z "$1" ]
then
    echo "Argument manquant. Fournissez une chaîne pour vérifier le fichier .env.<arg>"
    exit 1
fi

ENV_FILE=".env.$1"

if [ ! -f "$ENV_FILE" ]
then
    echo "Fichier $ENV_FILE manquant. Créez-le ou dupliquez le .env.local.dist en ajustant vos valeurs et réessayez"
    exit 1
fi