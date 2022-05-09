"Blueprint file containing the info command and some general button handlers for abort and back buttons"
# pylint: disable=unused-argument, missing-function-docstring
import os
from datetime import datetime
from math import floor

from flask_discord_interactions import DiscordInteractionsBlueprint, Embed, Message
from flask_discord_interactions.models.component import ActionRow, Button, ButtonStyles
from flask_discord_interactions.models.embed import Field, Footer, Media

import config
from resources import players

start_time = datetime.now()

system_bp = DiscordInteractionsBlueprint()


def get_info_embed() -> Embed:
    info_embed = Embed(
        title="Truck Simulator info",
        color=config.EMBED_COLOR,
        footer=Footer(
            text="Developer: r5#2253",
            icon_url="https://cdn.discordapp.com/avatars/692796548282712074/f298d263d8418edb25df0680a3371784.png",
        ),
        thumbnail=Media(url=config.SELF_AVATAR_URL),
        timestamp=datetime.utcnow().replace(microsecond=0).isoformat(),
    )

    uptime = datetime.now() - start_time
    days = uptime.days
    hours = floor(uptime.seconds / 3600)
    minutes = floor(uptime.seconds / 60) - hours * 60
    seconds = uptime.seconds - hours * 3600 - minutes * 60
    player_count = players.get_count("players")
    job_count = players.get_count("jobs")
    company_count = players.get_count("companies")
    system_info = (
        f"```Uptime: {days}d {hours}h {minutes}m {seconds}s\n"
        f"Registered Players: {player_count}\n"
        f"Running Jobs: {job_count}\n"
        f"Registered Companies: {company_count}```\n"
    )

    credits = (
        "<:lebogo:897861933418565652> **LeBogo**#3073 - _Testing helper_ - Contributed 2 lines of code\n"
        "<:panda:897860673898426462> **FlyingPanda**#0328 - _EPIC Artist_ - Drew almost all of the images you see "
        "(and had the idea of this bot)\n"
        "<:miri:897860673546117122> **Miriel**#0001 - _The brain_ - Gave a lot of great tips and constructive feedback"
    )

    links = (
        "**[Support server](https://discord.gg/FzAxtGTUhN)**\n"
        "**[Invite link](https://discord.com/api/oauth2/authorize?"
        "client_id=831052837353816066&scope=applications.commands%20bot)**\n"
        "**[Privacy Policy](https://trucksimulatorbot.rfive.de/privacypolicy.html)**\n"
        "**[Terms of Service](https://trucksimulatorbot.rfive.de/terms.html)**\n"
        "**[Github repository](https://github.com/therealr5/TruckSimulatorBot)**"
    )
    info_embed.fields = [
        Field(name="System information", value=system_info, inline=False),
        Field(name="Some useful links", value=links),
        Field(name="Credits", value=credits, inline=False),
    ]
    return info_embed


@system_bp.command()
def info(ctx) -> Message:
    """Prints out general information about the bot."""
    return Message(
        embed=get_info_embed(),
        components=[
            ActionRow(
                components=[
                    Button(
                        style=ButtonStyles.SECONDARY,
                        label="Refresh data",
                        custom_id=str(refresh),
                        emoji={"name": "reload", "id": 903581225149665290},
                    )
                ]
            )
        ],
    )


@system_bp.custom_handler(custom_id="refresh_system_info")
def refresh(ctx):
    return Message(embed=get_info_embed(), update=True)
