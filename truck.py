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
from flask_discord_interactions.models.embed import Field, Media, Author, Footer

import config

from resources import players
from resources import trucks
from resources import symbols

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


def get_truck_options() -> list[SelectMenuOption]:
    """Returns choices shown up in several truck commands"""
    choices = []
    for truck in trucks.get_all():
        choices.append(
            SelectMenuOption(
                label=truck.name,
                description=truck.description,
                value=str(truck.truck_id),
                emoji=symbols.parse_emoji(truck.emoji),
            )
        )
    return choices


def get_truck_components(player: players.Player) -> list[Component]:
    """Returns button and selects appearing underneath a truck embed"""
    return [
        ActionRow(
            components=[
                SelectMenu(
                    custom_id=["truck_view", player.id],
                    options=get_truck_options(),
                    placeholder="View details about a truck",
                )
            ]
        ),
        ActionRow(
            components=[
                SelectMenu(
                    custom_id=["truck_buy", player.id],
                    options=get_truck_options(),
                    placeholder="Buy a new truck",
                ),
            ]
        ),
        ActionRow(
            components=[
                Button(custom_id=["discard", player.id], label="Close Menu", style=ButtonStyles.SECONDARY),
            ]
        ),
    ]


@truck_bp.custom_handler(custom_id="discard")
def discard(ctx, player_id: int):
    """Remove all components"""
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    return Message(embeds=ctx.message.embeds, components=[], update=True)


@truck_bp.custom_handler(custom_id="back")
def show_truck_button(ctx, player_id: int):
    """Back-button"""
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    return show_truck(ctx, update=True)


@truck_bp.command()
def truck(ctx) -> Message:
    """View and manage your Truck"""
    return show_truck(ctx)


def show_truck(ctx, update: bool = False) -> Message:
    """Shows the main truck page"""
    player = players.get(ctx.author.id)
    # Detect, when the player is renamed
    if player.name != ctx.author.username:
        players.update(player, name=ctx.author.username)
    truck = trucks.get(player.truck_id)
    truck_embed = get_truck_embed(truck)
    truck_embed.author = Author(name=f"{player.name}'s truck", icon_url=ctx.author.avatar_url)
    return Message(embed=truck_embed, components=get_truck_components(player), update=update)


@truck_bp.custom_handler(custom_id="truck_buy")
def buy(ctx, player_id: int) -> Union[Message, str]:
    """Select handler to buy a new truck"""
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    if players.is_driving(int(ctx.author.id)):
        return f"{ctx.author.mention} You can't buy a new truck while you are driving in the old one"
    player = players.get(int(ctx.author.id))
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
                        custom_id=["back", player.id],
                        emoji=symbols.parse_emoji(new_truck.emoji),
                    )
                ]
            )
        ],
        update=True,
    )


@truck_bp.custom_handler(custom_id="truck_view")
def view(ctx, player_id: int) -> Message:
    """View details about a specific truck"""
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    truck_embed = get_truck_embed(trucks.get(int(ctx.values[0])))
    return Message(
        embed=truck_embed,
        components=[
            ActionRow(components=[Button(label="Back", custom_id=["back", player_id], style=ButtonStyles.SECONDARY)])
        ],
        update=True,
    )


@truck_bp.command()
def load(ctx) -> Message:
    """Shows what your Truck currently has loaded"""
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
