from random import randint, sample, choices
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.command import CommandOptionType
from flask_discord_interactions.models.component import ActionRow, Button, ButtonStyles
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field

import resources.players as players
import resources.items as items
import config

gambling_bp = DiscordInteractionsBlueprint()


@gambling_bp.command(
    options=[
        {
            "name": "side",
            "description": "The side you bet on",
            "type": CommandOptionType.STRING,
            "choices": [{"name": "heads", "value": "heads"}, {"name": "tails", "value": "tails"}],
            "required": True,
        },
        {"name": "amount", "description": "The amount you bet", "type": CommandOptionType.INTEGER, "required": True},
    ]
)
def coinflip(ctx, side: str, amount: int) -> str:
    """Test your luck while throwing a coin"""
    player = players.get(ctx.author.id)
    player.debit_money(amount)
    if randint(0, 1) == 0:
        result = "heads"
    else:
        result = "tails"

    if result == side:
        player.add_money(amount * 2)
        return "Congratulations, it was {}. You won ${}".format(result, "{:,}".format(amount))
    else:
        return "Nope, it was {}. You lost ${}".format(result, "{:,}".format(amount))


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
            Field(name="Result", value=":tada: Congratulations, you won ${:,} :tada:".format(amount * 10))
        )
        player.add_money(amount * 11)
    elif chosen_items.count(chosen_items[0]) == 2 or chosen_items.count(chosen_items[1]) == 2:
        slots_embed.fields.append(Field(name="Result", value="You won ${:,}".format(amount)))
        player.add_money(amount * 2)
    else:
        slots_embed.fields.append(Field(name="Result", value="You lost ${:,}".format(amount)))
    return slots_embed


@gambling_bp.custom_handler(custom_id="slots")
def slots_handler(ctx, author_id: int, amount: int) -> Message:
    if int(ctx.author.id) != author_id:
        return Message(deferred=True, update=True)
    return Message(
        embed=get_slots_embed(ctx.author, amount),
        update=True,
    )


@gambling_bp.command(annotations={"amount": "The amount you bet"})
def slots(ctx, amount: int) -> Message:
    """Simple slot machine"""
    return Message(
        embed=get_slots_embed(ctx.author, amount),
        components=[
            ActionRow(
                components=[
                    Button(
                        label="Spin again!",
                        custom_id=[slots_handler, ctx.author.id, amount],
                        style=ButtonStyles.SUCCESS,
                        emoji={"name": "🎰"},
                    )
                ]
            )
        ],
    )
