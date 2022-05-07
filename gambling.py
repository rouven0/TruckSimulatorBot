"Blueprint file containing all gambling-related commands and handlers"
# pylint: disable=unused-argument, missing-function-docstring
from random import choices, sample

from flask import request
from flask_discord_interactions import (DiscordInteractionsBlueprint, Embed,
                                        Message)
from flask_discord_interactions.context import Context
from flask_discord_interactions.discord import InteractionType
from flask_discord_interactions.models.component import (ActionRow, Button,
                                                         ButtonStyles,
                                                         TextInput)
from flask_discord_interactions.models.embed import Author, Field, Media
from flask_discord_interactions.models.modal import Modal

import config
from resources import components, items, players

gambling_bp = DiscordInteractionsBlueprint()


@gambling_bp.custom_handler(custom_id="casino")
def casino(ctx, player_id: str) -> Message:
    player = players.get(ctx.author.id, check=player_id)
    return Message(
        embed=Embed(
            title="Welcome to the casino",
            color=config.EMBED_COLOR,
            image=Media(
                url=(
                    "https://media.discordapp.net/attachments/868822515282231346/871394792947482674"
                    "/vegass-default_truck.png"
                )
            ),
        ),
        components=components.get_casino_buttons(player),
        update=True,
    )


def get_slots_embed(player: players.Player, amount: int) -> Embed:
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
        author=Author(name=f"{player.name}'s slots"),
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


def get_slots_components(player: players.Player, amount: int) -> list:
    return [
        ActionRow(
            components=[
                Button(
                    label="Spin again! (double amount)",
                    custom_id=[slots_handler, player.id, amount * 2],
                    style=ButtonStyles.SUCCESS,
                    emoji={"name": "🎰"},
                ),
                Button(
                    label="Spin again",
                    custom_id=[slots_handler, player.id, amount],
                    style=ButtonStyles.SECONDARY,
                ),
            ]
        ),
        ActionRow(components=[Button(label="Back", style=2, custom_id=["casino", player.id])]),
    ]


@gambling_bp.custom_handler(custom_id="slots_init")
def slots_modal(ctx, player_id):
    player = players.get(ctx.author.id, check=player_id)
    return Modal(
        custom_id=["slots", player.id],
        title="Spin a slot machine",
        components=[
            ActionRow(
                components=[
                    TextInput(
                        label="Amount", custom_id="input_amount", placeholder="The amount you want to bet. Can be 'all'"
                    )
                ]
            )
        ],
    )


@gambling_bp.custom_handler(custom_id="slots")
def slots_handler(ctx: Context, player_id: str, amount=0):
    player = players.get(ctx.author.id, check=player_id)
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    # replace this when pr is merged
    type = request.json.get("type")
    if type == InteractionType.MODAL_SUBMIT:
        amount = ctx.get_component("input_amount").value.replace(" ", "").replace("k", "000").replace("m", "000000")
        if amount == "all":
            amount = str(player.money)
    if str.isnumeric(amount):
        amount = int(amount)
    else:
        return Message("Invalid amount", ephemeral=True)
    return Message(
        embed=get_slots_embed(player, amount),
        components=get_slots_components(player, amount),
        update=True,
    )
