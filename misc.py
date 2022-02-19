# pylint: disable=unused-argument
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.embed import Field

import config

misc_bp = DiscordInteractionsBlueprint()


@misc_bp.command()
def support(ctx) -> str:
    """Truck Simulator support server"""
    return "https://discord.gg/FzAxtGTUhN"


@misc_bp.command()
def invite(ctx) -> Message:
    """Invite the Truck Simulator to your servers"""
    invite_embed = Embed(
        title="Click here to add the bot to your servers",
        description="Go spread the word of the Truck Simulator",
        url="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&scope=applications.commands",
        color=config.EMBED_COLOR,
    )
    return Message(embed=invite_embed)


@misc_bp.command()
def rules(ctx) -> Message:
    """Truck Simulator rules"""
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


@misc_bp.command()
def vote(ctx) -> Message:
    """Support the bot by voting for it on top.gg"""
    vote_embed = Embed(
        title="Click here to vote for the Truck Simulator",
        description="If you are a member of the official server, you will get a special color role",
        url="https://top.gg/bot/831052837353816066/vote",
        color=config.EMBED_COLOR,
    )
    return Message(embed=vote_embed)


@misc_bp.command()
def complain(ctx) -> str:
    """No description."""
    return (
        "What a crap bot this is! :rage: "
        "Hours of time wasted on this useless procuct of a terrible coder and a lousy artist "
        ":rage: :rage: Is this bot even TESTED before the updates are published... "
        "Horrible, just HORRIBLE this spawn of incopetence. Who tf made this? A 12 year old child? "
        "This child would probably have made it better than THAT :rage: "
    )
