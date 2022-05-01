install:
	@echo Setting up the virtual environment...
	@python3 -m venv venv
	@echo Installing requirements...
	@venv/bin/pip install -r requirements.txt
	@echo Done.
	@echo Setting up the systemd service...
	@sed -i 's|WORKINGDIRECTORY|'$(PWD)'|g' TruckSimulatorBot.service
	@sudo cp ./TruckSimulatorBot.service /etc/systemd/system
	@sudo systemctl daemon-reload
	@sudo systemctl enable TruckSimulatorBot.service
	@echo Done. The service is ready to be started

uninstall:
	@echo Removing systemd service...
	@sudo systemctl disable TruckSimulatorBot.service
	@sed -i 's|'$(PWD)'|WORKINGDIRECTORY|g' TruckSimulatorBot.service
	@sudo rm /etc/systemd/system/TruckSimulatorBot.service
	@sudo systemctl daemon-reload
	@echo Done.

start:
	@sudo systemctl start TruckSimulatorBot.service
	@echo Bot Service started

stop:
	@sudo systemctl stop TruckSimulatorBot.service
	@echo Bot Service stopped

restart:
	@sudo systemctl restart TruckSimulatorBot.service
	@echo Bot Service restarted

documentation:
	@venv/bin/sphinx-build -M html docs/ docs/_build/

