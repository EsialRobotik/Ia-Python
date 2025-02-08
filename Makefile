help: ## Affiche l'aide (commande par défaut)
	@bash .build/show_help.sh

coffee: ## Fait du café
	@echo "Eh oh tu m'as pris pour une cafetière ?"

checkenv: ## Vérifie l'environnement
	bash .build/check_load_env.sh

deploy: checkenv ## Déploie le code sur le robot
	bash .build/deploy.sh