"Blueprint file containing commands locked to the bot admins"
# pylint: disable=unused-argument,broad-except
import json

from flask_discord_interactions import DiscordInteractionsBlueprint, Permission, User
from flask_discord_interactions.models.message import Message, Embed

from resources import database
from resources import players
import config

admin_bp = DiscordInteractionsBlueprint()


@admin_bp.command(
    default_permission=False,
    permissions=[Permission(user=config.Users.ADMIN)],
    annotations={"query": "The query to execute."},
)
def sql(ctx, query: str):
    """Executes a sql query."""
    if ctx.author.id != config.Users.ADMIN:
        return "Wait. You shouldn't be able to even read this. Something is messed up."
    try:
        database.cur.execute(query)
        if database.cur.rowcount != 0:
            database.con.commit()
            return f"`Done. {database.cur.rowcount} row(s) affected`"
        return f"```json\n{json.dumps(database.cur.fetchall(), indent=2)}```"
    except Exception as error:
        return "Error: " + str(error)


blacklist = admin_bp.command_group(
    name="blacklist",
    description="Manage blacklisted users.",
    default_permission=False,
    permissions=[Permission(user=config.Users.ADMIN)],
)


@blacklist.command(annotations={"user": "The user to ban.", "reason": "The reason for this ban."})
def add(ctx, user: User, reason: str = "No reason provided."):
    """Adds a user to the blacklist."""
    try:
        player = players.get(user.id)
        player.xp = -1
        player.name = reason
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{user.username}** got blacklisted",
                color=config.EMBED_COLOR,
            )
        )
    except players.PlayerBlacklisted:
        return "Player already blacklisted."


@blacklist.command(annotations={"user": "The user to unban."})
def remove(ctx, user: User):
    """Removes a user from the blacklist."""
    try:
        players.get(user.id)
        return "That Player is not on the blacklist"
    except players.PlayerBlacklisted:
        player = players.Player(user.id, user.username, user.discriminator)
        player.xp = 0
        player.name = user.username
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{player.name}** got removed from the blacklist",
                color=config.EMBED_COLOR,
            )
        )
