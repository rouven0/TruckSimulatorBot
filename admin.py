# pylint: disable=unused-argument,broad-except
from flask_discord_interactions import DiscordInteractionsBlueprint, Permission, User
from flask_discord_interactions.models.message import Message, Embed

from resources import database
from resources import players
import config

admin_bp = DiscordInteractionsBlueprint()


@admin_bp.command(
    default_permission=False,
    permissions=[Permission(user=692796548282712074)],
    annotations={"query": "The query to execute."},
)
def sql(ctx, query: str):
    """Executes a sql query."""
    if int(ctx.author.id) != 692796548282712074:
        return "Wait. You shouldn't be able to even read this. Something is messed up"
    try:
        database.cur.execute(query)
        if database.cur.rowcount != 0:
            database.con.commit()
            return f"`Done. {database.cur.rowcount} row(s) affected`"
        return f"```\n{database.cur.fetchall()}```"
    except Exception as error:
        return "Error: " + str(error)


blacklist = admin_bp.command_group(
    name="blacklist",
    description="Manage blacklisted users.",
    default_permission=False,
    permissions=[Permission(user=692796548282712074)],
)


@blacklist.command(annotations={"user": "The user to ban.", "reason": "The reason for this ban."})
def add(ctx, user: User, reason: str = "No reason provided."):
    """Adds a user to the blacklist."""
    try:
        player = players.get(int(user.id))
        players.update(player, name=reason, xp=-1)
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
        players.get(int(user.id))
        return "That Player is not on the blacklist"
    except players.PlayerBlacklisted:
        player = players.Player(int(user.id), user.username)
        players.update(player, xp=0, name=user.username)
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{player.name}** got removed from the blacklist",
                color=config.EMBED_COLOR,
            )
        )


@admin_bp.command()
def complain(ctx) -> str:
    """No description."""
    return (
        "What a crap bot this is! :rage: "
        "Hours of time wasted on this useless procuct of a terrible coder and a lousy artist "
        ":rage: :rage: Is this bot even TESTED before the updates are published... "
        "Horrible, just HORRIBLE this spawn of incopetence. Who tf made this? A 12 year old child? "
        "This child would probably have made it better than THAT :rage: "
    )
