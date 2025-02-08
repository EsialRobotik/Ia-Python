# Script qui affiche l'aide du makefile : les commandes disponibles et à quoi elles servent

echo "Usage : "
cat Makefile | grep "## " | sed -r 's/([a-z]+:)[^#]+## (.+)/  \1 \2/g'