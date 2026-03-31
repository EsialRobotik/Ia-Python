help: ## Affiche l'aide (commande par défaut)
	@bash .build/show_help.sh

coffee: ## Fait du café
	@echo "Eh oh tu m'as pris pour une cafetière ?"

deploy-princess: ## Déploie le code sur le robot
	bash .build/check_load_env.sh princess
	bash .build/deploy-princess.sh

deploy-pami0: ## Déploie le code sur la pami0
	bash .build/check_load_env.sh pami0
	bash .build/deploy-pami0.sh

deploy-pami1: ## Déploie le code sur la pami1
	bash .build/check_load_env.sh pami1
	bash .build/deploy-pami1.sh

deploy-pami2: ## Déploie le code sur la pami2
	bash .build/check_load_env.sh pami2
	bash .build/deploy-pami2.sh

deploy-pami3: ## Déploie le code sur la pami3
	bash .build/check_load_env.sh pami3
	bash .build/deploy-pami3.sh