from dotenv import load_dotenv

load_dotenv("./.env")

from os import getenv
import sys

from flask import Flask
from flask_discord_interactions import DiscordInteractions

import logging
import resources.players as players
import config


app = Flask(__name__)
discord = DiscordInteractions(app)

app.config["DISCORD_CLIENT_ID"] = getenv("DISCORD_CLIENT_ID", default="")
app.config["DISCORD_PUBLIC_KEY"] = getenv("DISCORD_PUBLIC_KEY", default="")
app.config["DISCORD_CLIENT_SECRET"] = getenv("DISCORD_CLIENT_SECRET", default="")

if "--debug" in sys.argv:
    app.config["DONT_VALIDATE_SIGNATURE"]


logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)


# @discord.command()
# def ping(ctx):
# "Respond with a friendly 'pong'!"
# TODO stuff goes here


if "--update" in sys.argv:
    discord.update_commands(guild_id=830928381100556338)
    sys.exit()

discord.set_route(getenv("ROUTE", default=""))


if __name__ == "__main__":
    app.run(port=9001)
