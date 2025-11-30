help: ## Affiche l'aide (commande par défaut)
	@bash .build/show_help.sh

coffee: ## Fait du café
	@echo "Eh oh tu m'as pris pour une cafetière ?"

deploy-princess: ## Déploie le code sur le robot
	bash .build/check_load_env.sh princess
	bash .build/deploy-princess.sh

deploy-pami0: ## Déploie le code sur le robot
	bash .build/check_load_env.sh pami0
	bash .build/deploy-pami0.sh