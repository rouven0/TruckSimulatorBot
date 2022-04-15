"Blueprint file containing all truck-related commands and handlers"
# pylint: disable=unused-argument
from typing import Union
from math import log
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.component import (
    ActionRow,
    Button,
    ButtonStyles,
    Component,
    SelectMenu,
    SelectMenuOption,
)
from flask_discord_interactions.models.embed import Field, Media, Author

import config

from resources import players
from resources import trucks
from resources import symbols
from resources import components

truck_bp = DiscordInteractionsBlueprint()


def get_truck_embed(truck: trucks.Truck) -> Embed:
    """Returns an embed with details about the given Truck"""
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


@truck_bp.custom_handler(custom_id="manage_truck")
def show_truck_button(ctx, player_id: str):
    """Shows the main truck page"""
    player = players.get(ctx.author.id, check=player_id)
    # Detect, when the player is renamed
    if player.name != ctx.author.username:
        players.update(player, name=ctx.author.username)
    truck = trucks.get(player.truck_id)
    truck_embed = get_truck_embed(truck)
    truck_embed.author = Author(name=f"{player.name}'s truck", icon_url=ctx.author.avatar_url)
    return Message(embed=truck_embed, components=components.get_truck_components(player), update=True)


@truck_bp.custom_handler(custom_id="truck_buy")
def buy(ctx, player_id: str) -> Union[Message, str]:
    """Select handler to buy a new truck"""
    if players.is_driving(ctx.author.id):
        return "You can't buy a new truck while you are driving in the old one"
    player = players.get(ctx.author.id, check=player_id)
    old_truck = trucks.get(player.truck_id)
    new_truck = trucks.get(int(ctx.values[0]))
    selling_price = round(old_truck.price - (old_truck.price / 10) * log(player.truck_miles + 1))
    end_price = new_truck.price - selling_price
    # this also adds money if the end price is negative
    player.debit_money(end_price)
    players.update(player, truck_miles=0, gas=new_truck.gas_capacity, truck_id=new_truck.truck_id)
    answer_embed = Embed(
        description=f"You sold your old {old_truck.name} for ${selling_price} and bought a brand new {new_truck.name} "
        f"for ${new_truck.price}",
        color=config.EMBED_COLOR,
        author=Author(name="You got a new truck", icon_url=config.SELF_AVATAR_URL),
    )
    return Message(
        embed=answer_embed,
        components=[
            ActionRow(
                components=[
                    Button(
                        label="Check it out",
                        custom_id=["manage_truck", player.id],
                        emoji=symbols.parse_emoji(new_truck.emoji),
                    )
                ]
            )
        ],
        update=True,
    )


@truck_bp.custom_handler(custom_id="truck_view")
def view(ctx, player_id: str) -> Message:
    """View details about a specific truck"""
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    truck_embed = get_truck_embed(trucks.get(int(ctx.values[0])))
    return Message(
        embed=truck_embed,
        components=[
            ActionRow(
                components=[Button(label="Back", custom_id=["manage_truck", player_id], style=ButtonStyles.SECONDARY)]
            )
        ],
        update=True,
    )
