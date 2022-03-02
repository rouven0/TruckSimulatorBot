# pylint: disable=unused-argument, missing-function-docstring
from random import randint, sample, choices
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.option import CommandOptionType
from flask_discord_interactions.models.component import ActionRow, Button, ButtonStyles
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field
from flask_discord_interactions.models.autocomplete import Autocomplete

from resources import players
from resources import items
import config

gambling_bp = DiscordInteractionsBlueprint()


@gambling_bp.command(
    options=[
        {
            "name": "amount",
            "description": "The amount you bet. Must be a number except you bet all or half.",
            "type": CommandOptionType.INTEGER,
            "required": True,
            "autocomplete": True,
        },
        {
            "name": "side",
            "description": "The side you bet on.",
            "type": CommandOptionType.STRING,
            "choices": [{"name": "heads", "value": "heads"}, {"name": "tails", "value": "tails"}],
            "required": True,
        },
    ]
)
def coinflip(ctx, side: str, amount: int) -> str:
    """Test your luck while throwing a coin."""
    player = players.get(ctx.author.id)
    player.debit_money(amount)
    if randint(0, 1) == 0:
        result = "heads"
    else:
        result = "tails"

    if result == side:
        player.add_money(amount * 2)
        return f"Congratulations, it was {result}. You won ${amount:,}"
    return f"Nope, it was {result}. You lost ${amount:,}"


def get_slots_embed(author: User, amount: int) -> Embed:
    player = players.get(int(author.id))
    player.debit_money(amount)

    chosen_items = choices(sample(items.get_all(), 8), k=3)
    machine = "<|"
    for item in chosen_items:
        machine += f"<:n:{item.emoji}>"
        machine += "|"
    machine += ">"

    slots_embed = Embed(
        description=machine,
        color=config.EMBED_COLOR,
        author=Author(name=f"{author.username}'s slots", icon_url=author.avatar_url),
        fields=[],
    )

    if chosen_items.count(chosen_items[0]) == 3:
        slots_embed.fields.append(
            Field(name="Result", value=f":tada: Congratulations, you won ${amount * 10:,} :tada:")
        )
        player.add_money(amount * 11)
    elif chosen_items.count(chosen_items[0]) == 2 or chosen_items.count(chosen_items[1]) == 2:
        slots_embed.fields.append(Field(name="Result", value=f"You won ${amount:,}"))
        player.add_money(amount * 2)
    else:
        slots_embed.fields.append(Field(name="Result", value=f"You lost ${amount:,}"))
    return slots_embed


def get_slots_components(user: User, amount: int) -> list:
    return [
        ActionRow(
            components=[
                Button(
                    label="Spin again! (double amount)",
                    custom_id=[slots_handler, user.id, amount * 2],
                    style=ButtonStyles.SUCCESS,
                    emoji={"name": "🎰"},
                ),
                Button(
                    label="Spin again",
                    custom_id=[slots_handler, user.id, amount],
                    style=ButtonStyles.SECONDARY,
                ),
            ]
        )
    ]


@gambling_bp.custom_handler(custom_id="slots")
def slots_handler(ctx, author_id: int, amount: int) -> Message:
    if int(ctx.author.id) != author_id:
        return Message(deferred=True, update=True)
    return Message(
        embed=get_slots_embed(ctx.author, amount),
        components=get_slots_components(ctx.author, amount),
        update=True,
    )


@gambling_bp.command(annotations={"amount": "The amount you bet. Must be a number except you want to bet all or half."})
def slots(ctx, amount: Autocomplete(int)):
    """Simple slot machine."""
    if amount == 0:
        return "You can't spin the machine with that little money you inserted. At least try to do proper gambling."
    return Message(
        embed=get_slots_embed(ctx.author, amount),
        components=get_slots_components(ctx.author, amount),
    )


def amount_all(ctx, amount, side=None):
    """Let 'all' be an int option"""
    player = players.get(ctx.author.id)
    if len(amount.value) == 0:
        return [{"name": "all", "value": player.money}, {"name": "half", "value": round(player.money / 2)}]
    return []


gambling_bp.add_autocomplete_handler(amount_all, "slots")
gambling_bp.add_autocomplete_handler(amount_all, "coinflip")
