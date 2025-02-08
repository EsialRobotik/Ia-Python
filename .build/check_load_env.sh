# Script qui vérifie la présence des fichiers de config

if [ ! -f .env.local ]
then
    echo "Fichier .en.local manquant. Dupliquez le .env.local.dist en ajustant vos valeurs et réessayez"
    exit 1
fi