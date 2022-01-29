from dotenv import load_dotenv

load_dotenv("./.env")

from os import getenv
import sys

from flask import Flask
from flask_discord_interactions import DiscordInteractions, Message, Embed
from flask_discord_interactions.models.embed import Field

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


@discord.command()
def support(ctx) -> str:
    """
    Truck Simulator support server
    """
    return "https://discord.gg/FzAxtGTUhN"


@discord.command()
def invite(ctx) -> Message:
    """
    Invite the truck simulator to your servers
    """
    support_embed = Embed(
        title="Click here to add the bot to your servers",
        description="Go spread the word of the Truck Simulator",
        url="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&scope=applications.commands",
        color=config.EMBED_COLOR,
    )
    return Message(embed=support_embed)


@discord.command()
def rules(ctx) -> Message:
    """
    Truck Simulator rules
    """
    rules_embed = Embed(title="Truck Simulator Ingame Rules", color=config.EMBED_COLOR, fields=[])
    rules_embed.fields.append(
        Field(
            name="Trading ingame currency for real money",
            value="Not only that it is pretty stupid to trade real world's money in exchange of a number "
            "somewhere in a random database it will also get you banned from this bot.",
            inline=False,
        )
    )
    rules_embed.fields.append(
        Field(
            name="Autotypers",
            value="Don't even try, it's just wasted work only to get you blacklisted.",
        )
    )
    return Message(embed=rules_embed)


@discord.command()
def vote(ctx) -> Message:
    """
    Support the bot by voting for it on top.gg
    """
    vote_embed = Embed(
        title="Click here to vote for the Truck Simulator",
        description="If you are a member of the official server, you will get a special color role",
        url="https://top.gg/bot/831052837353816066/vote",
        color=config.EMBED_COLOR,
    )
    return Message(embed=vote_embed)


@discord.command()
def complain(ctx) -> str:
    return (
        "What a crap bot this is! :rage: "
        "Hours of time wasted on this useless procuct of a terrible coder and a lousy artist "
        ":rage: :rage: Is this bot even TESTED before the updates are published... "
        "Horrible, just HORRIBLE this spawn of incopetence. Who tf made this? A 12 year old child? "
        "This child would probably have made it better than THAT :rage: "
    )


if "--update" in sys.argv:
    discord.update_commands(guild_id=830928381100556338)
    sys.exit()

if "deploy" in sys.argv:
    discord.update_commands()
    sys.exit()

discord.set_route(getenv("ROUTE", default=""))

if __name__ == "__main__":
    app.run(port=9001)
