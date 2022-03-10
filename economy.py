# pylint: disable=unused-argument,missing-function-docstring
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field, Footer

from resources import players
from resources import places
from resources import items
from resources import jobs
from resources import symbols
from resources import trucks

import config


economy_bp = DiscordInteractionsBlueprint()


@economy_bp.custom_handler(custom_id="job_show")
def show_job(ctx, player_id: int) -> Message:
    player = players.get(player_id)

    current_job = player.get_job()
    if current_job is None:
        return Message(deferred=True, update=True)
    job_embed = Embed(
        color=config.EMBED_COLOR,
        author=Author(name=f"{player}'s Job"),
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
def refill(ctx, player_id: int):
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


@economy_bp.command(annotations={"user": "The user you want to give money to.", "amount": "The amount you give."})
def give(ctx, user: User, amount: int) -> Message:
    """Gives money to a user."""
    amount = abs(int(amount))
    acceptor = players.get(int(user.id))

    donator = players.get(ctx.author.id)
    if int(ctx.author.id) == acceptor.id:
        return Message(
            embed=Embed(
                title=f"Hey {ctx.author.username}",
                description="You can't give money to yourself!",
                color=config.EMBED_COLOR,
            )
        )
    donator.debit_money(amount)
    acceptor.add_money(amount)
    return Message(embed=Embed(description=f"{donator} gave ${amount} to {acceptor}", color=config.EMBED_COLOR))


@economy_bp.command()
def minijobs(ctx) -> Message:
    """Prints out all permanently running minijobs."""
    player = players.get(int(ctx.author.id))
    minijob_list = ""
    for place in places.get_all():
        if place.accepted_item is not None:
            minijob_list += (
                f"\n{symbols.LIST_ITEM}**{place}** will give you "
                f"${place.item_reward*(player.level+1):,} if you bring them *{place.accepted_item}*."
            )
    return Message(embed=Embed(title="All available minijobs", description=minijob_list, color=config.EMBED_COLOR))
