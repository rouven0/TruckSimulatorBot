"Blueprint file containing commands locked to the bot admins"
# pylint: disable=unused-argument,broad-except
import json
from threading import Thread

import requests

import config
import mysql.connector
from flask_discord_interactions import DiscordInteractionsBlueprint, User
from flask_discord_interactions.context import Context
from flask_discord_interactions.models.message import Embed, Message
from resources import players

admin_bp = DiscordInteractionsBlueprint()


@admin_bp.command(
    default_member_permissions=8,
    annotations={"query": "The query to execute."},
)
def sql(ctx: Context, query: str):
    """Executes a sql query."""
    if ctx.author.id != config.Users.ADMIN:
        return "Wait. You shouldn't be able to even read this. Something is messed up."
    try:
        with mysql.connector.connect(**config.DATABASE_ARGS) as con:
            with con.cursor(dictionary=True) as cur:
                cur.execute(query)
                if cur.rowcount != 0:
                    con.commit()
                    return f"`Done. {cur.rowcount} row(s) affected`"
                return f"```json\n{json.dumps(cur.fetchall(), indent=2)}```"
    except Exception as error:
        return "Error: " + str(error)


blacklist = admin_bp.command_group(
    name="blacklist",
    description="Manage blacklisted users.",
    default_member_permissions=4,
)


@blacklist.command(annotations={"user": "The user to ban.", "reason": "The reason for this ban."})
def add(ctx: Context, user: User, reason: str = "No reason provided."):
    """Adds a user to the blacklist."""
    try:
        player = players.get(user.id)
        player.xp = -1
        player.name = reason
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{user.username}** got blacklisted.",
                color=config.EMBED_COLOR,
            ),
            ephemeral=True,
        )
    except players.PlayerBlacklisted:
        return Message("Player already blacklisted.", ephemeral=True)


@blacklist.command(annotations={"user": "The user to unban."})
def remove(ctx: Context, user: User):
    """Removes a user from the blacklist."""
    try:
        players.get(user.id)
        return Message("That Player is not on the blacklist.", ephemeral=True)
    except players.PlayerBlacklisted:
        player = players.Player(user.id, user.username, user.discriminator)
        player.xp = 0
        player.name = user.username
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{player.name}** got removed from the blacklist.",
                color=config.EMBED_COLOR,
            ),
            ephemeral=True,
        )


@blacklist.command()
def show(ctx: Context) -> Message:
    """Show the blacklist."""
    blacklisted_players = players.get_blacklisted()
    return Message(
        embed=Embed(
            color=config.EMBED_COLOR,
            title="All blacklisted players",
            description="".join([f"▫️ <@{player.id}> - {player.name}\n" for player in blacklisted_players]),
        ),
        ephemeral=True,
    )


@admin_bp.command()
def ping(ctx: Context) -> str:
    """Checks the Api latency."""
    start_time = int(ctx.id) >> 22

    def measure_time():
        end_time = int(requests.get(ctx.followup_url(message="@original")).json()["id"]) >> 22
        ctx.send(f"{end_time - start_time} ms")

    Thread(target=measure_time).start()
    return "Pong"
