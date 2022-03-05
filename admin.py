# pylint: disable=unused-argument,broad-except
from flask_discord_interactions import DiscordInteractionsBlueprint, Permission
from flask_discord_interactions.models.message import Message, Embed
from flask_discord_interactions.models.embed import Field

from resources import database
from resources import players
import config

admin_bp = DiscordInteractionsBlueprint()


@admin_bp.command(default_permission=False, permissions=[Permission(user=692796548282712074)])
def sql(ctx, query: str):
    """DANGER: Execute raw sql"""
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


@blacklist.command()
def add(ctx, user: str, reason: str):
    """Add a user to the blacklist."""
    try:
        player = players.get(int(user))
        players.update(player, name=reason, xp=-1)
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{player.name}** got blacklisted",
                color=config.EMBED_COLOR,
            )
        )
    except players.PlayerBlacklisted:
        return "Player already blacklisted"


@blacklist.command()
def remove(ctx, user: str):
    """Remove a user from the blacklist."""
    try:
        players.get(int(user))
        return "That Player is not on the blacklist"
    except players.PlayerBlacklisted:
        player = players.Player(user, "Unknown")
        players.update(player, xp=0, name="Unknown player")
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{player.id}** got removed from the blacklist",
                color=config.EMBED_COLOR,
            )
        )


@admin_bp.command()
def serverrules(ctx) -> Message:
    """Truck Simulator server Rules."""
    rules_embed = Embed(title="Truck Simulator Server Rules", color=config.EMBED_COLOR, fields=[])
    rules_embed.fields.append(
        Field(
            name="Be civil and respectful",
            value="Treat everyone with respect. Absolutely no harassment, witch hunting, sexism, racism, "
            "or hate speech will be tolerated.",
            inline=False,
        )
    )
    rules_embed.fields.append(
        Field(
            name="No spam or self-promotion",
            value="No spam or self-promotion (server invites, advertisements, etc) without permission "
            "from a staff member. This includes DMing fellow members.",
            inline=False,
        )
    )
    rules_embed.fields.append(
        Field(
            name="No NSFW or obscene content",
            value="This includes text, images, or links featuring nudity, sex, hard violence, "
            "or other graphically disturbing content.",
            inline=False,
        )
    )
    return Message(embed=rules_embed)
