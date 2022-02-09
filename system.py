from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.embed import Field, Footer, Media
from flask_discord_interactions.models.component import ActionRow, Button, ButtonStyles

from datetime import datetime
from math import floor

import config
import resources.players as players


start_time = datetime.now()

system_bp = DiscordInteractionsBlueprint()


def get_info_embed() -> Embed:
    info_embed = Embed(
        title="Truck Simulator info",
        color=config.EMBED_COLOR,
        footer=Footer(text="Developer: r5#2253"),
        thumbnail=Media(url=config.SELF_AVATAR_URL),
    )

    uptime = datetime.now() - start_time
    days = uptime.days
    hours = floor(uptime.seconds / 3600)
    minutes = floor(uptime.seconds / 60) - hours * 60
    seconds = uptime.seconds - hours * 3600 - minutes * 60
    player_count = players.get_count("players")
    driving_player_count = players.get_count("driving_players")
    job_count = players.get_count("jobs")
    company_count = players.get_count("companies")
    system_info = (
        f"```Uptime: {days}d {hours}h {minutes}m {seconds}s\n"
        f"Registered Players: {player_count}\n"
        f"Running Jobs: {job_count}\n"
        f"Registered Companies: {company_count}\n"
        f"Driving Trucks: {driving_player_count}```"
    )

    credits = (
        "<:lebogo:897861933418565652> LeBogo#3073 - _Testing helper_ - Contributed 2 lines of code\n"
        "<:panda:897860673898426462> FlyingPanda#0328 - _EPIC Artist_ - Drew almost all of the images you see (and had the idea of this bot)\n"
        "<:miri:897860673546117122> Miriel#0001 - _The brain_ - Gave a lot of great tips and constructive feedback"
    )
    info_embed.fields = [
        Field(name="System information", value=system_info, inline=False),
        Field(name="Credits", value=credits, inline=False),
    ]
    return info_embed


@system_bp.command()
def info(ctx) -> Message:
    """System information and credits"""
    return Message(
        embed=get_info_embed(),
        components=[
            ActionRow(
                components=[
                    Button(
                        style=ButtonStyles.SECONDARY,
                        label="Refresh data",
                        custom_id=refresh,
                        emoji={"name": "reload", "id": 903581225149665290},
                    )
                ]
            )
        ],
    )


@system_bp.custom_handler(custom_id="refresh_system_info")
def refresh(ctx):
    return Message(embed=get_info_embed(), update=True)
