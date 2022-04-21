install:
	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install -r requirements.txt
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorBot.service
	@sudo cp ./TruckSimulatorBot.service /etc/systemd/system
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorTimeouts.service
	@sudo cp ./TruckSimulatorTimeouts.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@sudo systemctl enable TruckSimulatorBot.service
	@sudo systemctl enable TruckSimulatorTimeouts.service
	@echo Done. The services are ready to be started

uninstall:
	@echo Removing systemd services...
	@sudo systemctl disable TruckSimulatorBot.service
	@sudo systemctl disable TruckSimulatorTimeouts.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorBot.service
	@sudo rm /etc/systemd/system/TruckSimulatorBot.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorTimeouts.service
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

