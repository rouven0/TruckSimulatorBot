# pylint: disable=unused-argument,missing-function-docstring
import traceback
import sys
from os import getenv
import logging

from dotenv import load_dotenv

from flask import Flask, json
from flask_discord_interactions import DiscordInteractions, Message
from werkzeug.exceptions import HTTPException

load_dotenv("./.env")
from admin import admin_bp
from system import system_bp
from stats import profile_bp
from driving import driving_bp
from economy import economy_bp
from misc import misc_bp
from gambling import gambling_bp
from guide import guide_bp
from truck import truck_bp
from companies import company_bp

from resources import players
import config


app = Flask(__name__)
discord = DiscordInteractions(app)

app.config["DISCORD_CLIENT_ID"] = getenv("DISCORD_CLIENT_ID", default="")
app.config["DISCORD_PUBLIC_KEY"] = getenv("DISCORD_PUBLIC_KEY", default="")
app.config["DISCORD_CLIENT_SECRET"] = getenv("DISCORD_CLIENT_SECRET", default="")

if "--debug" in sys.argv:
    app.config["DONT_VALIDATE_SIGNATURE"] = True


logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)


@app.errorhandler(players.NotEnoughMoney)
def not_enough_money(error):
    return Message(
        content="You don't have enough money to do this.",
    ).dump()


@app.errorhandler(players.NotDriving)
def not_driving(error):
    return {"type": 6}


@app.errorhandler(players.PlayerNotRegistered)
def not_registered(error):
    return Message(
        content=f"<@{error.requested_id}> You are not registered yet. Try `/profile register` to get started",
        ephemeral=True,
    ).dump()


@app.errorhandler(players.PlayerBlacklisted)
def blacklisted(error: players.PlayerBlacklisted):
    return Message(
        content=f"<@{error.requested_id}> You are blacklisted for the following reason: {error.reason}", ephemeral=True
    ).dump()


@app.errorhandler(Exception)
def general_error(error):
    logging.error(error)
    traceback.print_tb(error.__traceback__)
    return Message(
        content=f"Looks like we got an error here. ```{error.__class__.__name__}: {error}```"
        "If this occurs multiple times feel free to report it in the support server"
    ).dump()


@app.errorhandler(HTTPException)
def handle_exception(error):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = error.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "code": error.code,
            "name": error.name,
            "description": error.description,
        }
    )
    response.content_type = "application/json"
    return response


if "--remove-global" in sys.argv:
    discord.update_commands()
    sys.exit()

if "--admin" in sys.argv:
    discord.register_blueprint(admin_bp)
    discord.update_commands(guild_id=839580174282260510)
    sys.exit()

discord.register_blueprint(system_bp)
discord.register_blueprint(profile_bp)
discord.register_blueprint(driving_bp)
discord.register_blueprint(economy_bp)
discord.register_blueprint(misc_bp)
discord.register_blueprint(gambling_bp)
discord.register_blueprint(guide_bp)
discord.register_blueprint(truck_bp)
discord.register_blueprint(company_bp)

if "--update" in sys.argv:
    discord.update_commands(guild_id=830928381100556338)
    sys.exit()

if "--deploy" in sys.argv:
    discord.update_commands()
    sys.exit()

discord.register_blueprint(admin_bp)

discord.set_route("/interactions")

if __name__ == "__main__":
    app.run(port=9001, debug=True)
