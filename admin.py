from flask_discord_interactions import DiscordInteractionsBlueprint, Permission
from flask_discord_interactions.models.message import Message, Embed

import resources.database as database
import resources.players as players
import config

admin_bp = DiscordInteractionsBlueprint()


@admin_bp.command(default_permission=False, permissions=[Permission(user=692796548282712074)])
def sql(ctx, query: str):
    if int(ctx.author.id) != 692796548282712074:
        return "Wait. You shouldn't be able to even read this. Something is messed up"
    try:
        database.cur.execute(query)
        if database.cur.rowcount != 0:
            database.con.commit()
            return f"`Done. {database.cur.rowcount} row(s) affected`"
        else:
            return f"```\n{database.cur.fetchall()}```"
    except Exception as e:
        return "Error: " + str(e)


blacklist = admin_bp.command_group(
    name="blacklist", default_permission=False, permissions=[Permission(user=692796548282712074)]
)


@blacklist.command()
def add(ctx, user: str, reason: str):
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
    try:
        players.get(int(user))
        return "Player not on blacklist"
    except players.PlayerBlacklisted:
        player = players.Player(user, "Unknown")
        players.update(player, xp=0, name="Unknown player")
        return Message(
            embed=Embed(
                description=f":white_check_mark: **{player.id}** got removed from the blacklist",
                color=config.EMBED_COLOR,
            )
        )
