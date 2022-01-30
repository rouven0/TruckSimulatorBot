from typing import Union
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed, User
from flask_discord_interactions.models.command import CommandOptionType
from flask_discord_interactions.models.embed import Field, Media, Author, Footer
from math import log

import config

import resources.players as players
import resources.trucks as trucks
import resources.symbols as symbols

truck_bp = DiscordInteractionsBlueprint()


def get_truck_embed(truck: trucks.Truck) -> Embed:
    """
    Returns an embed with details about the given Truck
    """
    truck_embed = Embed(
        title=truck.name,
        description=truck.description,
        color=config.EMBED_COLOR,
        image=Media(url=truck.image_url),
        fields=[],
    )
    truck_embed.fields.append(Field(name="Gas consumption", value=f"{truck.gas_consumption} litres per mile"))
    truck_embed.fields.append(Field(name="Gas capacity", value=str(truck.gas_capacity) + " l"))
    truck_embed.fields.append(Field(name="Price", value="$" + str(truck.price)))
    truck_embed.fields.append(Field(name="Loading capacity", value=f"{truck.loading_capacity} items"))
    return truck_embed


def get_truck_choices() -> list[dict]:
    choices = []
    for truck in trucks.get_all():
        choices.append({"name": truck.name, "value": truck.truck_id})
    return choices


truck = truck_bp.command_group(name="truck", description="Do stuff with your truck")


@truck.command()
def show(ctx, user: User = None) -> Message:
    """
    Get details about your truck and the trucks of your friends
    """
    if user is not None:
        player = players.get(int(user.id))
        avatar_url = user.avatar_url
    else:
        player = players.get(ctx.author.id)
        avatar_url = ctx.author.avatar_url
    # Detect, when the player is renamed
    if player.name != ctx.author.username:
        players.update(player, name=ctx.author.username)
    truck = trucks.get(player.truck_id)
    truck_embed = get_truck_embed(truck)
    truck_embed.author = Author(name="{}'s truck".format(player.name), icon_url=avatar_url)
    truck_embed.footer = Footer(
        icon_url=config.SELF_AVATAR_URL,
        text="See all trucks with `/truck list` and change your truck with `/truck buy`",
    )
    return Message(embed=truck_embed)


@truck.command(
    options=[
        {
            "name": "truck",
            "description": "The truck you want to buy",
            "type": CommandOptionType.INTEGER,
            "required": True,
            "choices": get_truck_choices(),
        }
    ],
)
def buy(ctx, truck: int) -> Union[Message, str]:
    """
    Buy a new truck, your old one will be sold and your miles will be reset
    """
    if players.is_driving(int(ctx.author.id)):
        return f"{ctx.author.mention} You can't buy a new truck while you are driving in the old one"
    player = players.get(int(ctx.author.id))
    old_truck = trucks.get(player.truck_id)
    new_truck = trucks.get(truck)
    selling_price = round(old_truck.price - (old_truck.price / 10) * log(player.truck_miles + 1))
    end_price = new_truck.price - selling_price
    # this also adds money if the end price is negative
    player.debit_money(end_price)
    players.update(player, truck_miles=0, gas=new_truck.gas_capacity, truck_id=new_truck.truck_id)
    answer_embed = Embed(
        description=f"You sold your old {old_truck.name} for ${selling_price} and bought a brand new {new_truck.name} for ${new_truck.price}",
        color=config.EMBED_COLOR,
        author=Author(name="You got a new truck", icon_url=config.SELF_AVATAR_URL),
        footer=Footer(text="Check out your new baby with `/truck show`"),
    )
    return Message(embed=answer_embed)


@truck.command(
    options=[
        {
            "name": "truck",
            "description": "The truck you want to view",
            "type": CommandOptionType.INTEGER,
            "required": True,
            "choices": get_truck_choices(),
        }
    ],
)
def view(ctx, truck) -> Message:
    """
    View details about a specific truck
    """
    truck_embed = get_truck_embed(trucks.get(truck))
    truck_embed.footer = Footer(
        icon_url=config.SELF_AVATAR_URL,
        text="See all trucks with `/truck list` and change your truck with `/truck buy`",
    )
    return Message(embed=truck_embed)


@truck.command()
def list(ctx) -> Message:
    """
    Lists all available Trucks
    """
    list_embed = Embed(
        title="All available trucks",
        color=config.EMBED_COLOR,
        footer=Footer(
            text="Get more information about a truck with `/truck view <id>`", icon_url=config.SELF_AVATAR_URL
        ),
        fields=[],
    )
    for truck in trucks.get_all():
        list_embed.fields.append(
            Field(name=truck.name, value="Id: {} \n Price: ${:,}".format(truck.truck_id, truck.price), inline=False)
        )
    return Message(embed=list_embed)


@truck_bp.command()
def load(ctx) -> Message:
    """
    Shows what your Truck currently has loaded
    """
    player = players.get(int(ctx.author.id))
    item_list = ""
    if len(player.loaded_items) == 0:
        item_list = "Your truck is empty"
    else:
        for item in player.loaded_items:
            item_list += f"{symbols.LIST_ITEM} <:placeholder:{item.emoji}> {item.name}\n"
    load_embed = Embed(
        title="Your currently loaded items",
        description=item_list,
        color=config.EMBED_COLOR,
        footer=Footer(text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}"),
    )
    return Message(embed=load_embed)
