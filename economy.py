"Blueprint file containing all economy-related commands and handlers"
# pylint: disable=unused-argument,missing-function-docstring
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.option import CommandOptionType
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field, Footer

from resources import players
from resources import items
from resources import jobs
from resources import trucks
from resources import levels

import config


economy_bp = DiscordInteractionsBlueprint()


@economy_bp.custom_handler(custom_id="job_show")
def show_job(ctx, player_id: str) -> Message:
    player = players.get(player_id)

    current_job = player.get_job()
    if current_job is None:
        raise players.WrongPlayer()
    job_embed = Embed(
        color=config.EMBED_COLOR,
        author=Author(name=f"{player.name}'s Job"),
        fields=[],
    )
    place_from = current_job.place_from
    place_to = current_job.place_to
    item = items.get(place_from.produced_item)
    job_message = f"Bring {item} from {place_from.name} to {place_to.name}."
    job_embed.fields.append(Field(name="Current job", value=job_message, inline=False))
    job_embed.fields.append(Field(name="Current state", value=jobs.get_state(current_job)))
    return Message(embed=job_embed, ephemeral=True)


@economy_bp.custom_handler(custom_id="refill")
def refill(ctx, player_id: str):
    player = players.get_driving_player(ctx.author.id, check=player_id)
    gas_amount = trucks.get(player.truck_id).gas_capacity - player.gas
    price = round(gas_amount * 1.2)

    try:
        player.debit_money(price)
    except players.NotEnoughMoney:
        if player.gas < 170:
            if player.level > 2:
                players.update(
                    player,
                    gas=player.gas + 100,
                    level=player.level - 2,
                    xp=0,
                )
            else:
                players.update(player, gas=player.gas + 100, xp=0)
            return Message(
                f"{ctx.author.mention} We have a problem: You don't have enough money. Lets make a deal. "
                "I will give you 100 litres of gas, and you lose 2 levels",
                ephemeral=True,
            )
        return Message(
            f"{ctx.author.mention} you don't have enough money to do this. "
            "Do some jobs and come back if you have enough",
            ephemeral=True,
        )

    refill_embed = Embed(
        title="Thank you for visiting our gas station",
        description=f"You filled {gas_amount} litres into your truck and payed ${price}",
        color=config.EMBED_COLOR,
        footer=Footer(text="Current gas price: $1.2 per litre"),
    )

    players.update(player, gas=trucks.get(player.truck_id).gas_capacity)
    drive_embed: Embed = ctx.message.embeds[0]
    drive_embed.fields[2]["value"] = str(player.gas)

    return Message(embeds=[drive_embed, refill_embed], update=True)


@economy_bp.command(
    options=[
        {
            "name": "user",
            "description": "The user you want to give the money to.",
            "type": CommandOptionType.USER,
            "required": True,
        },
        {
            "name": "amount",
            "description": "The amount you want to give.",
            "type": CommandOptionType.INTEGER,
            "min_value": 1,
            "max_value": 1000000,
            "required": True,
        },
    ]
)
def give(ctx, user: User, amount: int) -> Message:
    """Transfers money to a specific user."""
    acceptor = players.get(user.id)
    donator = players.get(ctx.author.id)

    if ctx.author.id == acceptor.id:
        return Message(
            embed=Embed(
                title=f"Hey {ctx.author.username}",
                description="You can't give money to yourself!",
                color=config.EMBED_COLOR,
            )
        )

    cap = levels.coincap(acceptor.level)
    if amount > cap:
        return Message(
            embed=Embed(
                title=f"Hey {ctx.author.username}",
                description=f"You can't give more than ${cap:,} to this user.",
                color=config.EMBED_COLOR,
            )
        )

    donator.debit_money(amount)
    acceptor.add_money(amount)
    return Message(embed=Embed(description=f"{donator.name} gave ${amount} to {acceptor}", color=config.EMBED_COLOR))
