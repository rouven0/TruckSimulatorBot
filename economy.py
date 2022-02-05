from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field, Footer

import resources.players as players
import resources.places as places
import resources.items as items
import resources.jobs as jobs
import resources.symbols as symbols
import resources.trucks as trucks

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
        author=Author(name="{}'s Job".format(player.name)),
        fields=[],
    )
    place_from = current_job.place_from
    place_to = current_job.place_to
    item = items.get(place_from.produced_item)
    job_message = "Bring <:placeholder:{}> {} from {} to {}.".format(
        item.emoji, item.name, place_from.name, place_to.name
    )
    job_embed.fields.append(Field(name="Current job", value=job_message, inline=False))
    job_embed.fields.append(Field(name="Current state", value=jobs.get_state(current_job)))
    return Message(embed=job_embed, ephemeral=True)


@economy_bp.custom_handler(custom_id="job_new")
def new_job(ctx, player_id: int) -> Message:
    player = players.get_driving_player(ctx.author.id, check=player_id)
    job_embed = Embed(
        color=config.EMBED_COLOR,
        author=Author(name="{}'s Job".format(ctx.author.username), icon_url=ctx.author.avatar_url),
        fields=[],
    )
    job = jobs.generate(player)
    player.add_job(job)

    drive_embed: Embed = ctx.message.embeds[0]
    orig_components = ctx.message.components
    drive_embed.fields.append(
        Field(name="Navigation: Drive to {}".format(job.place_from.name), value=str(job.place_from.position))
    )
    orig_components[2]["components"][0]["disabled"] = True
    orig_components[2]["components"][1]["disabled"] = False

    # parse the components to objects again
    components = []
    for actionRow in orig_components:
        for c in actionRow["components"]:
            c.pop("hash")
        components.append(ActionRow(components=[Button(**c) for c in actionRow["components"]]))

    item = items.get(job.place_from.produced_item)
    job_message = "{} needs <:placeholder:{}> {} from {}. You get ${:,} for this transport".format(
        job.place_to.name, item.emoji, item.name, job.place_from.name, job.reward
    )
    job_embed.fields.append(Field(name="You got a new Job", value=job_message, inline=False))
    job_embed.fields.append(Field(name="Current state", value=jobs.get_state(job)))
    return Message(embeds=[drive_embed, job_embed], components=components, update=True)


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
        else:
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

    orig_components = ctx.message.components
    # parse the components to objects again
    components = []
    for actionRow in orig_components:
        for c in actionRow["components"]:
            c.pop("hash")
        components.append(ActionRow(components=[Button(**c) for c in actionRow["components"]]))
    return Message(embeds=[drive_embed, refill_embed], components=components)


@economy_bp.command()
def give(ctx, user: User, amount: int) -> Message:
    """
    Do I really have to explain this?
    """
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
    return Message(
        embed=Embed(description=f"{donator.name} gave ${amount} to {acceptor.name}", color=config.EMBED_COLOR)
    )


@economy_bp.command()
def minijobs(ctx) -> Message:
    """
    Prints out all permanently running minijobs
    """
    player = players.get(int(ctx.author.id))
    minijob_list = ""
    for place in places.get_all():
        if place.accepted_item is not None:
            minijob_list += f"\n{symbols.LIST_ITEM}**{place.name}** will give you ${place.item_reward*(player.level+1):,} if you bring them *{place.accepted_item}*."
    return Message(embed=Embed(title="All available minijobs", description=minijob_list, color=config.EMBED_COLOR))
