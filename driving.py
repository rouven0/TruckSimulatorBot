# pylint: disable=unused-argument,missing-function-docstring
from datetime import datetime
from time import time

import requests

from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.context import Context
from flask_discord_interactions.models.component import ActionRow, Button, SelectMenu, SelectMenuOption
from flask_discord_interactions.models.embed import Author, Field, Footer, Media

import config
from resources import players
from resources import companies
from resources import items
from resources import levels
from resources import places
from resources import symbols
from resources import assets
from resources import jobs
from resources import trucks

driving_bp = DiscordInteractionsBlueprint()


def get_drive_embed(player: players.Player, avatar_url: str) -> Embed:
    """Returns the drive embed that includes all the information about the current position and gas"""
    place = places.get(player.position)
    all_companies = companies.get_all()
    drive_embed = Embed(
        description="Even more stable now",
        color=config.EMBED_COLOR,
        timestamp=datetime.utcnow().replace(microsecond=0).isoformat(),
        author=Author(name=f"{player.name} is driving", icon_url=avatar_url),
        footer=Footer(text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}"),
        fields=[],
    )

    drive_embed.fields.append(Field(name="Minimap", value=generate_minimap(player, all_companies), inline=False))
    drive_embed.fields.append(Field(name="Position", value=str(player.position)))
    drive_embed.fields.append(Field(name="Gas left", value=f"{player.gas} l"))

    current_job = player.get_job()
    if current_job is not None:
        if current_job.state == 0:
            navigation_place = current_job.place_from
        else:
            navigation_place = current_job.place_to
        drive_embed.fields.append(
            Field(name=f"Navigation: Drive to {navigation_place.name}", value=str(navigation_place.position))
        )

    if place.image_url_default is not None:
        drive_embed.fields.append(
            Field(
                name="What is here?",
                value=f"<:placeholder:{items.get(place.produced_item).emoji}> {place.name}",
                inline=False,
            )
        )
        drive_embed.image = Media(url=assets.get_place_image(player, place))
    else:
        drive_embed.image = Media(url=assets.get_default(player))
    if player.position in [c.hq_position for c in all_companies]:
        for company in all_companies:
            if company.hq_position == player.position:
                drive_embed.fields.append(
                    Field(
                        name="What is here?",
                        value=f"A company called **{company.name}**",
                        inline=False,
                    )
                )
    return drive_embed


def generate_minimap(player: players.Player, all_companies: list[companies.Company]) -> str:
    """Generate the minimap shown in /drive"""
    minimap_array = []
    for i in range(0, 7):
        minimap_array.append([])
        for j in range(0, 7):
            minimap_array[i].append("")
            position = [player.position[0] - 3 + j, player.position[1] + 3 - i]
            map_place = places.get(position)
            # show other trucks on the map
            try:
                item = items.get(map_place.produced_item)
            except items.ItemNotFound:
                item = None
            if item is not None:
                minimap_array[i][j] = f"<:placeholder:{items.get(map_place.produced_item).emoji}>"
            elif position in [c.hq_position for c in all_companies]:
                for company in all_companies:
                    if company.hq_position == position:
                        minimap_array[i][j] = company.logo
            elif position[0] in [-1, config.MAP_BORDER + 1] or position[1] in [-1, config.MAP_BORDER + 1]:
                # Mark the map border with symbols
                minimap_array[i][j] = ":small_orange_diamond:"
                if (
                    # Small correction mechanism to prevent the lines from going beyond the border
                    position[0] < -1
                    or position[0] > config.MAP_BORDER + 1
                    or position[1] < -1
                    or position[1] > config.MAP_BORDER + 1
                ):
                    minimap_array[i][j] = symbols.MAP_BACKGROUND
            else:
                minimap_array[i][j] = symbols.MAP_BACKGROUND
                for plr in players.get_all_driving_players():
                    if plr.position == position:
                        minimap_array[i][j] = trucks.get(plr.truck_id).emoji

    minimap_array[3][3] = trucks.get(player.truck_id).emoji
    minimap = ""
    for i in range(0, 7):
        for j in range(0, 7):
            minimap = minimap + minimap_array[i][j]
        minimap = minimap + "\n"
    return minimap


def get_buttons(player: players.Player) -> list:
    """Returns buttons based on the players position"""
    buttons = []
    directional_buttons = []
    place = places.get(player.position)
    for symbol in symbols.get_all_drive_symbols():
        if symbol in symbols.get_drive_position_symbols(player.position):
            directional_buttons.append(
                Button(style=1, emoji={"name": "placeholder", "id": symbol}, custom_id=[str(symbol), player.id])
            )
        else:
            directional_buttons.append(
                Button(style=1, emoji={"name": "placeholder", "id": symbol}, custom_id=str(symbol), disabled=True)
            )
    directional_buttons.append(
        Button(style=4, emoji={"name": "stop", "id": symbols.STOP}, custom_id=["stop", player.id])
    )
    buttons.append(ActionRow(components=directional_buttons))

    current_job = player.get_job()
    load_disabled = not len(player.loaded_items) < trucks.get(player.truck_id).loading_capacity
    unload_disabled = not len(player.loaded_items) > 0
    if place.name == "Nothing":
        load_disabled = True
        unload_disabled = True

    action_buttons = [
        Button(
            style=1,
            emoji={"name": "load", "id": symbols.LOAD},
            custom_id=["load", player.id],
            disabled=load_disabled,
        ),
        Button(
            style=1,
            emoji={"name": "unload", "id": symbols.UNLOAD},
            custom_id=["unload", player.id],
            disabled=unload_disabled,
        ),
        Button(
            style=2,
            label="Show loaded items",
            custom_id=["show_load", player.id],
        ),
    ]

    if "refill" in place.available_actions:
        action_buttons.append(
            Button(style=2, emoji={"name": "refill", "id": symbols.REFILL}, custom_id=["refill", player.id])
        )

    buttons.append(ActionRow(components=action_buttons))
    buttons.append(
        ActionRow(
            components=[
                Button(style=3, label="New Job", custom_id=["job_new", player.id], disabled=(current_job is not None)),
                Button(style=2, label="Show Job", custom_id=["job_show", player.id], disabled=(current_job is None)),
            ]
        )
    )
    return buttons


@driving_bp.custom_handler(custom_id="stop")
def stop(ctx, player_id: int):
    player = players.get_driving_player(ctx.author.id, check=player_id)
    player.stop_drive()
    return Message(
        embeds=ctx.message.embeds,
        components=[],
        update=True,
    )


@driving_bp.custom_handler(custom_id="load")
def load(ctx, player_id: int):
    player = players.get_driving_player(ctx.author.id, check=player_id)
    player.update(int(time()), ctx.followup_url())

    item = items.get(places.get(player.position).produced_item)
    if item.name not in [i.name for i in player.loaded_items]:
        player.load_item(item)
    job_message = None

    current_job = player.get_job()
    if current_job is not None and item.name == current_job.place_from.produced_item:
        current_job.state = jobs.STATE_LOADED
        job_message = jobs.get_state(current_job)
        player.update_job(current_job, state=current_job.state)

    drive_embed = get_drive_embed(player, ctx.author.avatar_url)
    drive_embed.fields.append(
        Field(
            name="Loading successful",
            value=f"You loaded <:placeholder:{item.emoji}> {item.name} into your truck",
            inline=False,
        )
    )
    if job_message is not None:
        return Message(
            embeds=[drive_embed, Embed(title="Job Notification", description=job_message, color=config.EMBED_COLOR)],
            update=True,
        )
    return Message(embed=drive_embed, components=get_buttons(player), update=True)


@driving_bp.custom_handler(custom_id="unload")
def unload(ctx, player_id: int):
    player = players.get_driving_player(ctx.author.id, check=player_id)
    player.update(int(time()), ctx.followup_url())

    drive_embed = get_drive_embed(player, ctx.author.avatar_url)
    item_options: list[SelectMenuOption] = []
    for item in player.loaded_items:
        if item.name not in [o.value for o in item_options]:
            item_options.append(
                SelectMenuOption(
                    label=item.name,
                    value=item.name,
                    emoji={"name": item.name, "id": item.emoji},
                )
            )
    select = SelectMenu(
        custom_id=["unload_items", player.id],
        placeholder="Choose which items to unload",
        options=item_options,
        min_values=1,
        max_values=len(item_options),
    )
    cancel_button = Button(custom_id=["cancel", player.id], label="Cancel", style=4)
    return Message(
        embed=drive_embed,
        components=[ActionRow(components=[select]), ActionRow(components=[cancel_button])],
        update=True,
    )


@driving_bp.custom_handler(custom_id="unload_items")
def unload_items(ctx, player_id: int):
    player = players.get_driving_player(ctx.author.id, check=player_id)

    item_string = ""
    for name in ctx.values:
        item = items.get(name)
        player.unload_item(item)
        if name == ctx.values[0]:
            item_string += f"<:placeholder:{item.emoji}> {item.name}"
        elif name == ctx.values[-1]:
            item_string += f" and <:placeholder:{item.emoji}> {item.name}"
        else:
            item_string += f", <:placeholder:{item.emoji}> {item.name}"

    place = places.get(player.position)
    current_job = player.get_job()
    drive_embed = get_drive_embed(player, ctx.author.avatar_url)

    drive_embed.fields.append(
        Field(name="Unloading successful", value=f"You removed {item_string} from your truck", inline=False)
    )

    message = Message(embed=drive_embed, components=get_buttons(player), update=True)

    # add a notification embed if a job is done
    if (
        current_job is not None
        and current_job.place_from.produced_item in ctx.values
        and player.position == current_job.place_to.position
    ):
        current_job.state = jobs.STATE_DONE
        player.add_money(current_job.reward)
        player.remove_job(current_job)
        job_message = jobs.get_state(current_job) + player.add_xp(levels.get_job_reward_xp(player.level))
        if player.company is not None:
            company = companies.get(player.company)
            company.add_net_worth(int(current_job.reward / 10))
            job_message += f"\nYour company's net worth was increased by ${int(current_job.reward/10):,}"
        # get the drive embed egain to fit the job update
        drive_embed = get_drive_embed(player, ctx.author.avatar_url)
        message.embeds = [
            drive_embed,
            Embed(title="Job Notification", description=job_message, color=config.EMBED_COLOR),
        ]

    # add a notification embed if a minijob is done
    if place.accepted_item in ctx.values and place.item_reward:
        player.add_money(place.item_reward)
        message.embeds.append(
            Embed(
                title="Minijob Notification",
                description=(
                    f"{place.name} gave you ${place.item_reward * (player.level + 1):,} for bringing them "
                    f"{place.accepted_item}"
                ),
                color=config.EMBED_COLOR,
            )
        )

    return message


@driving_bp.custom_handler(custom_id="cancel")
def cancel(ctx, player_id: int):
    player = players.get_driving_player(ctx.author.id, check=player_id)
    return Message(embed=get_drive_embed(player, ctx.author.avatar_url), components=get_buttons(player), update=True)


@driving_bp.custom_handler(custom_id=str(symbols.LEFT))
def left(ctx, player_id: int):
    return move(ctx, symbols.LEFT, player_id)


@driving_bp.custom_handler(custom_id=str(symbols.UP))
def up(ctx, player_id: int):
    return move(ctx, symbols.UP, player_id)


@driving_bp.custom_handler(custom_id=str(symbols.DOWN))
def down(ctx, player_id: int):
    return move(ctx, symbols.DOWN, player_id)


@driving_bp.custom_handler(custom_id=str(symbols.RIGHT))
def right(ctx, player_id: int):
    return move(ctx, symbols.RIGHT, player_id)


def move(ctx: Context, direction, player_id):
    """Centralized function for all the directional buttons"""
    player = players.get_driving_player(int(ctx.author.id), player_id)

    if direction == symbols.LEFT:
        player.position = [player.position[0] - 1, player.position[1]]

    if direction == symbols.UP:
        player.position = [player.position[0], player.position[1] + 1]

    if direction == symbols.DOWN:
        player.position = [player.position[0], player.position[1] - 1]

    if direction == symbols.RIGHT:
        player.position = [player.position[0] + 1, player.position[1]]

    player.miles += 1
    player.truck_miles += 1
    player.gas -= trucks.get(player.truck_id).gas_consumption

    if player.gas <= 0:
        try:
            player.debit_money(3000)
        except players.NotEnoughMoney:
            pass
        players.update(player, gas=trucks.get(player.truck_id).gas_capacity, position=[7, 7])
        player.stop_drive()
        return Message(
            content=(
                "You messed up and ran out of gas. Your company had to have your truck towed away. "
                "You will pay $3000 for this incident!"
            ),
            components=[],
            update=True,
        )

    player.update(int(time()), ctx.followup_url())
    players.update(
        player,
        position=player.position,
        miles=player.miles,
        truck_miles=player.truck_miles,
        gas=player.gas,
    )

    return Message(embed=get_drive_embed(player, ctx.author.avatar_url), components=get_buttons(player), update=True)


@driving_bp.command()
def drive(ctx) -> Message:
    """Start driving your Truck."""
    player = players.get(ctx.author.id)
    # Detect, when the player is renamed
    if player.name != ctx.author.username:
        players.update(player, name=ctx.author.username)

    if players.is_driving(ctx.author.id):
        driving_player = players.get_driving_player(ctx.author.id)
        requests.patch(url=driving_player.followup_url + "/messages/@original", json={"components": []})
        driving_player.stop_drive()

    player = players.DrivingPlayer(
        **vars(players.get(ctx.author.id)), followup_url=ctx.followup_url(), last_action_time=int(time())
    )
    player.start_drive()
    return Message(
        embed=get_drive_embed(player, ctx.author.avatar_url),
        components=get_buttons(player),
    )


@driving_bp.custom_handler(custom_id="show_load")
def load_show(ctx, player_id: int) -> Message:
    """Shows what your Truck currently has loaded"""
    player = players.get_driving_player(int(ctx.author.id), check=player_id)
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
    return Message(embed=load_embed, ephemeral=True)
