install:
ifeq (, $(wildcard ./resources/players.db))
	@echo Setting up player database...
	@cp ./templates/template_players.db ./resources/players.db
	@echo Done.
else
	@echo Found existing player database, skipping this step.
endif

ifeq (, $(wildcard ./.env))
	@echo Setting up the environment file
	@cp ./templates/template_env .env
	@read -p "Enter bot token: " token; \
	sed -i 's|<TOKEN>|'$$token'|g' .env
	@echo Done.
else
	@echo Found existing environment, skipping this step.
endif

	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install -r requirements.txt
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorBot.service
	@sed -i 's|USER|'$(USER)'|g' TruckSimulatorBot.service
	@sudo cp ./TruckSimulatorBot.service /etc/systemd/system
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorApi.service
	@sed -i 's|USER|'$(USER)'|g' TruckSimulatorApi.service
	@sudo cp ./TruckSimulatorApi.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@echo Done. The services are ready to be started

uninstall:
	@echo Removing systemd services...
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorBot.service
	@sed -i 's|'$(USER)'|USER|g' TruckSimulatorBot.service
	@sudo rm /etc/systemd/system/TruckSimulatorBot.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorApi.service
	@sed -i 's|'$(USER)'|USER|g' TruckSimulatorApi.service
	@sudo rm /etc/systemd/system/TruckSimulatorApi.service
	@sudo systemctl daemon-reload
	@echo Done.

start-bot:
	@sudo systemctl start TruckSimulatorBot.service
	@echo Bot Service started

stop-bot:
	@sudo systemctl stop TruckSimulatorBot.service
	@echo Bot Service stopped

start-api:
	@sudo systemctl start TruckSimulatorApi.service
	@echo Api Service started

stop-api:
	@sudo systemctl stop TruckSimulatorApi.service
	@echo Api Service stopped

