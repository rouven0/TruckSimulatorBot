"""
This module provides several lists of buttons and selects
"""
from flask_discord_interactions.models.component import (
    ActionRow,
    Button,
    SelectMenu,
    SelectMenuOption,
)
from i18n import t
from trucksimulator.resources import companies, items, places, symbols, trucks
from trucksimulator.resources.companies import Company
from trucksimulator.resources.players import Player


def back_home(player_id) -> Button:
    "Returns a simple 'back' button that opens the home screen"
    return Button(
        style=2,
        label=t("back"),
        custom_id=["home", player_id],
    )


def back_to_road(player_id) -> Button:
    "Returns a 'back to the road' button that opens the drive screen"
    return Button(
        custom_id=["continue_drive", player_id],
        style=3,
        label=t("back_road"),
        emoji={"name": "logo_round", "id": "955233759278559273"},
    )


def get_drive_buttons(player: Player) -> list:
    """
    Returns a list of buttons for the drive menu
    :param player: The player to get the buttons for
    :return: A list of buttons
    """
    buttons = []
    directional_buttons = []
    place = places.get(player.position)
    current_job = player.get_job()
    for symbol in symbols.get_all_drive_symbols():
        if symbol in symbols.get_drive_position_symbols(player.position):
            directional_buttons.append(
                Button(
                    style=1
                    if current_job is not None and places.get_direction(player, current_job.target_place) == symbol
                    else 2,
                    emoji={"name": "placeholder", "id": symbol},
                    custom_id=[str(symbol), player.id],
                )
            )
        else:
            directional_buttons.append(
                Button(
                    style=2,
                    emoji={"name": "placeholder", "id": symbol},
                    custom_id=str(symbol),
                    disabled=True,
                )
            )
    buttons.append(ActionRow(components=directional_buttons))

    load_disabled = not len(player.loaded_items) < trucks.get(player.truck_id).loading_capacity
    unload_disabled = not len(player.loaded_items) > 0
    if not place:
        load_disabled = True
        unload_disabled = True

    action_buttons = [
        Button(
            style=1
            if current_job
            and place
            and current_job.state == 0
            and int(place.position) == int(current_job.place_from.position)
            else 2,
            emoji={"name": "load", "id": symbols.LOAD},
            custom_id=["load", player.id],
            disabled=load_disabled,
            label=t("driving.buttons.load"),
        ),
        Button(
            style=1
            if current_job
            and place
            and current_job.state == 1
            and int(place.position) == int(current_job.place_to.position)
            else 2,
            emoji={"name": "unload", "id": symbols.UNLOAD},
            custom_id=["unload", player.id],
            disabled=unload_disabled,
            label=t("driving.buttons.unload"),
        ),
    ]

    if place and "refill" in place.available_actions:
        action_buttons.append(
            Button(
                style=2,
                label=t("driving.buttons.refill"),
                emoji={"name": "refill", "id": symbols.REFILL},
                custom_id=["refill", player.id],
            )
        )
    if place and "gambling" in place.available_actions:
        action_buttons.append(
            Button(
                style=3,
                label=t("casino.enter"),
                custom_id=["casino", player.id],
                emoji={"name": "money", "id": items.get(place.produced_item).emoji},
            )
        )

    buttons.append(ActionRow(components=action_buttons))
    buttons.append(
        ActionRow(
            components=[
                Button(
                    style=1 if current_job is None else 2,
                    label=t("driving.buttons.job.new"),
                    custom_id=["job_new", player.id],
                    disabled=(current_job is not None),
                ),
                Button(
                    style=2,
                    label=t("driving.buttons.job.show"),
                    custom_id=["job_show", player.id],
                    disabled=(current_job is None),
                ),
                Button(
                    style=3,
                    label=t("driving.buttons.home"),
                    custom_id=["home", player.id],
                ),
            ]
        )
    )

    return buttons


def get_home_buttons(player: Player) -> list:
    """
    Returns a list of buttons for the home menu
    :param player: The player to get the buttons for
    :return: A list of buttons
    """
    return [
        ActionRow(
            components=[
                Button(
                    custom_id=["manage_truck", player.id],
                    style=2,
                    label=t("home.truck"),
                    emoji=symbols.parse_emoji(trucks.get(player.truck_id).emoji),
                ),
                Button(
                    custom_id=["manage_company", player.id],
                    style=2,
                    label=t("home.company"),
                    emoji=symbols.parse_emoji(companies.get(player.company).logo)
                    if player.company
                    else {"name": "🏛️", "id": None},
                ),
                Button(
                    custom_id=["top", player.id],
                    style=2,
                    label=t("home.leaderboard"),
                    emoji={"name": "🏆", "id": None},
                ),
            ]
        ),
        ActionRow(components=[back_to_road(player.id)]),
    ]


def get_company_buttons(player: Player, company: Company) -> list:
    """
    Returns a list of buttons for the company menu
    :param player: The player to get the buttons for
    :param company: The company to get the buttons for
    :return: A list of buttons
    """
    components = [
        ActionRow(
            components=[
                Button(
                    label=t("company.components.update"),
                    custom_id=["company_update", player.id],
                    style=2,
                    disabled=(player.id != company.founder),
                ),
                Button(
                    label=t("company.components.leave"),
                    custom_id=["company_leave", player.id],
                    style=4,
                    disabled=(player.id == company.founder),
                ),
            ]
        ),
        ActionRow(components=[back_home(player.id)]),
    ]
    company_members = company.get_members()
    if len(company_members) > 1:
        components.insert(
            1,
            ActionRow(
                components=[
                    SelectMenu(
                        placeholder=t("company.components.fire"),
                        custom_id=["company_fire", player.id],
                        options=[
                            SelectMenuOption(label=f"{plr.name}#{plr.discriminator}", value=plr.id)
                            for plr in company.get_members()
                            if plr.id != player.id
                        ],
                        disabled=(player.id != company.founder),
                    )
                ]
            ),
        )
    return components


def get_truck_components(player: Player) -> list:
    """
    Returns a list of buttons for the truck menu
    :param player: The player to get the buttons for
    :return: A list of buttons
    """
    return [
        ActionRow(
            components=[
                SelectMenu(
                    custom_id=["truck_view", player.id],
                    options=get_truck_options(),
                    placeholder=t("truck.view.placeholder"),
                )
            ]
        ),
        ActionRow(components=[back_home(player.id)]),
    ]


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


def get_casino_buttons(player) -> list:
    """
    Returns a list of buttons for the casino menu
    :param player: The player to get the buttons for
    :return: A list of buttons
    """
    return [
        ActionRow(
            components=[
                Button(
                    custom_id=["slots_init", player.id],
                    style=2,
                    label=t("casino.slots.modal.title"),
                    emoji={"name": "🎰", "id": None},
                ),
                Button(
                    custom_id=["blackjack", player.id],
                    style=2,
                    label=t("coming_soon"),
                    emoji={"name": "♠️", "id": None},
                    disabled=True,
                ),
            ]
        ),
        ActionRow(components=[back_to_road(player.id)]),
    ]
