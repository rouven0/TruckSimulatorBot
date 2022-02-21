# pylint: disable=unused-argument,wrong-import-position
import traceback
import sys
from os import getenv
import logging

from dotenv import load_dotenv
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.embed import Embed, Footer
from flask_discord_interactions import DiscordInteractions, Message

load_dotenv("./.env")

from flask import Flask, json, request, abort
import requests
from werkzeug.exceptions import HTTPException

from resources import players
from resources import items
import config

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


# not made for public use, only for myself to get some webhooks and literally just copied from the discord docs
# @app.route("/webhooks")
# def webhook():
# data = {
# "client_id": getenv("DISCORD_CLIENT_ID", default=""),
# "client_secret": getenv("DISCORD_CLIENT_SECRET", default=""),
# "grant_type": "authorization_code",
# "code": request.args.get("code"),
# "redirect_uri": "https://trucksimulatorbot.rfive.de/api/beta/webhooks",
# }
# headers = {"Content-Type": "application/x-www-form-urlencoded"}
# r = requests.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers)
# r.raise_for_status()
# return r.json()


@app.route("/votes", methods=["POST"])
def votes():
    """Handle vote webhooks from top.gg"""
    if request.headers.get("Authorization") != getenv("VOTE_AUTHORIZATION"):
        abort(401)
    voter_id = int(request.json.get("user"))
    if not players.registered(voter_id):
        vote_message_content = (
            f"Hmm, somebody voted that isn't even registered <:cat:892088956253011989> (id: {voter_id})"
        )
    else:
        player = players.get(voter_id)
        if player.id == 619879176316649482:
            player.load_item(items.get("cheese"))
        added_money = (player.level + 1) * 100
        player.add_money(added_money)
        vote_message_content = (
            f"**{player.name}** just voted for the Truck Simulator. As a reward they received ${added_money}."
        )
    vote_message = Message(
        embed=Embed(
            title="Thank you for voting for the Truck Simulator",
            description=vote_message_content
            + "\n\n You can vote [here](https://top.gg/bot/831052837353816066/vote) every 12 hours.",
            color=config.EMBED_COLOR,
        )
    )
    requests.post(url=getenv("VOTE_WEBHOOK", ""), json=vote_message.dump()["data"])
    return "", 204


@app.errorhandler(players.NotEnoughMoney)
def not_enough_money(error):
    """Error handler in case a player doesn't have enough money"""
    return Message(
        content="You don't have enough money to do this.",
    ).dump()


@app.errorhandler(players.NotDriving)
def not_driving(error):
    """Defer buttons if the wrong player clicked them"""
    return {"type": 6}


@app.errorhandler(players.PlayerNotRegistered)
def not_registered(error):
    """Error handler in case a player isn't found in the database"""
    return Message(
        content=f"<@{error.requested_id}> You are not registered yet. Try `/profile` to get started",
        ephemeral=True,
    ).dump()


@app.errorhandler(players.PlayerBlacklisted)
def blacklisted(error: players.PlayerBlacklisted):
    """Error handler in case a player is on the blalist"""
    return Message(
        content=f"<@{error.requested_id}> You are blacklisted for the following reason: {error.reason}", ephemeral=True
    ).dump()


@app.errorhandler(Exception)
def general_error(error):
    """Log any error to journal and to discord"""
    logging.error(error)
    traceback.print_tb(error.__traceback__)
    return Message(
        embed=Embed(
            title="Looks like we got an error here.",
            description=f" ```py\n {error.__class__.__name__}: {error}```",
            footer=Footer(
                text="If this occurs multiple times feel free to report it.",
                icon_url=config.SELF_AVATAR_URL,
            ),
            color=int("ff0000", 16),
        ),
        components=[
            ActionRow(components=[Button(style=5, label="Support Server", url="https://discord.gg/FzAxtGTUhN")])
        ],
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
