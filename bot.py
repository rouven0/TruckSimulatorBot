from dotenv import load_dotenv
from flask_discord_interactions.models.embed import Embed
from werkzeug.exceptions import HTTPException

load_dotenv("./.env")

from os import getenv
import sys

from flask import Flask, json
from flask_discord_interactions import DiscordInteractions, Message

import logging
import resources.players as players
import config

from stats import profile_bp
from misc import misc_bp

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
    return Message(
        embed=Embed(
            title="Whoops, Looks like we got an error here", description=f"**{error.__class__.__name__}** ```{error}```"
        )
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


discord.register_blueprint(profile_bp)
discord.register_blueprint(misc_bp)

if "--update" in sys.argv:
    discord.update_commands(guild_id=830928381100556338)
    sys.exit()

if "--deploy" in sys.argv:
    discord.update_commands()
    sys.exit()


discord.set_route(getenv("ROUTE", default=""))

if __name__ == "__main__":
    app.run(port=9001)
