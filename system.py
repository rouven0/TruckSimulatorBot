"Blueprint file containing the info command and some general button handlers for abort and back buttons"
# pylint: disable=unused-argument, missing-function-docstring
from datetime import datetime
from math import floor

from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.embed import Field, Footer, Media
from flask_discord_interactions.models.component import ActionRow, Button, ButtonStyles

import config
from resources import players


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
        "<:panda:897860673898426462> FlyingPanda#0328 - _EPIC Artist_ - Drew almost all of the images you see "
        "(and had the idea of this bot)\n"
        "<:miri:897860673546117122> Miriel#0001 - _The brain_ - Gave a lot of great tips and constructive feedback"
    )

    links = (
        "**[Support server](https://discord.gg/FzAxtGTUhN)**\n"
        "**[Invite link](https://discord.com/api/oauth2/authorize?"
        "client_id=831052837353816066&scope=applications.commands)**\n"
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


@system_bp.custom_handler(custom_id="discard")
def discard(ctx, player_id: str):
    """General handler to remove all components"""
    if ctx.author.id != player_id:
        return Message(deferred=True, update=True)
    return Message(embeds=ctx.message.embeds, components=[], update=True)


@system_bp.command()
def vote(ctx) -> Message:
    """Returns a link to vote for this bot on top.gg."""
    player = players.get(ctx.author.id)
    vote_embed = Embed(
        title="Click here to vote for the Truck Simulator",
        description="As a reward, you will get double xp for 30 minutes.",
        url="https://top.gg/bot/831052837353816066/vote",
        color=config.EMBED_COLOR,
        fields=[Field(name="Your last vote", value=f"<t:{player.last_vote}:R>")],
    )
    return Message(embed=vote_embed)
