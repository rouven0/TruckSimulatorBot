REQUIREMENTS=$()
install:
ifeq (, $(wildcard ./players.db))
	@echo Setting up player database...
	@cp ./templates/template_players.db players.db
	@echo Done.
else
	@echo Found existing player database, skipping this step.
endif

ifeq (, $(wildcard ./.env))
	@echo Setting up the environment file
	@cp ./templates/template_env .env
	@read -p "Enter bot token: " token; \
	sed -i 's|TOKEN|'$$token'|g' .env
	@echo Done.
else
	@echo Found existing environment, skipping this step.
endif

	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install $(shell cat ./requirements.txt)
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorBot.service
	@sudo cp ./TruckSimulatorBot.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@echo Done. The service is ready to be started

uninstall:
	@echo Removing systemd service...
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorBot.service
	@sudo rm /etc/systemd/system/TruckSimulatorBot.service
	@sudo systemctl daemon-reload
	@echo Done.
