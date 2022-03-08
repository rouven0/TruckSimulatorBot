[![Pylint](https://github.com/therealr5/TruckSimulatorBot/actions/workflows/pylint.yml/badge.svg)](https://github.com/therealr5/TruckSimulatorBot/actions/workflows/pylint.yml)
[![License](https://img.shields.io/github/license/therealr5/TrucksimulatorBot)](https://github.com/therealr5/TruckSimulatorBot/blob/http-only/LICENSE)
[![Black](https://img.shields.io/badge/codestyle-black-000000)](https://github.com/psf/black)
[![Discord](https://img.shields.io/discord/839580174282260510)](https://discord.gg/FzAxtGTUhN)

# TruckSimulatorBot
Small Truck Simulator app using the [flask-discord-interactions](https://github.com/Breq16/flask-discord-interactions) library

## Self-host this bot
### Install
Simply install and set up this bot using `make`.
Before, please provide a .env file containing the following variables:
```env
DISCORD_CLIENT_ID
DISCORD_PUBLIC_KEY
DISCORD_CLIENT_SECRET
MYSQL_HOST
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
VOTE_WEBHOOK
```

Superuser permissions are required to set up the bot's systemd service

### Remove the bot
Use `make uninstall` to remove the bot's systemd service before you delete the bot directory.

## Projekt Description

### Basic controls
The virtual map is the heart of the Truck Simulator. Everything is a place that you can drive to. Some commands are bound to specific places, some are available everywhere.

After you are registered, simply start a drive by hitting `/drive`. You will see a minimap, a detailed view of the place you're at and some buttons to move your truck on the map.

### Jobs
After you claimed a Job, you have to bring an item from one place to another.
Drive to the first place, load your Truck, drive to the second place and you're done. The reward depends on your current level.

### Gas system
Always keep an eye on your gas, it will be pretty expensive if you don't. If you are low on gas, simply drive to the gas station in the middle of the map and refill you truck.
The gas prices are refreshed daily and can be seen in the support server.

### Trucks
As soon as you have enough money, you can buy a new Truck. Better ones are expensive, but have better stats when it comes to gas capacity and consumption.
When you buy a new truck, your old one will be sold; the selling price is based on its original price and the miles you drove with this truck.
