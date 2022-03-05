install:
	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install -r requirements.txt
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorBot.service
	@sed -i 's|USER|'$(USER)'|g' TruckSimulatorBot.service
	@sudo cp ./TruckSimulatorBot.service /etc/systemd/system
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorTimeouts.service
	@sed -i 's|USER|'$(USER)'|g' TruckSimulatorTimeouts.service
	@sudo cp ./TruckSimulatorTimeouts.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@echo Done. The services are ready to be started

uninstall:
	@echo Removing systemd services...
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorBot.service
	@sed -i 's|'$(USER)'|USER|g' TruckSimulatorBot.service
	@sudo rm /etc/systemd/system/TruckSimulatorBot.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorTimeouts.service
	@sed -i 's|'$(USER)'|USER|g' TruckSimulatorTimeouts.service
	@sudo rm /etc/systemd/system/TruckSimulatorTimeouts.service
	@sudo systemctl daemon-reload
	@echo Done.

start:
	@sudo systemctl start TruckSimulatorBot.service
	@sudo systemctl start TruckSimulatorTimeouts.service
	@echo Bot Service started

stop:
	@sudo systemctl stop TruckSimulatorBot.service
	@sudo systemctl stop TruckSimulatorTimeouts.service
	@echo Bot Service stopped

documentation:
	@sphinx-build -M html docs/ docs/_build/

