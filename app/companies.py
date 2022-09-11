"Blueprint file containing all company-related commands and handlers"
# pylint: disable=unused-argument
import re

import config
from flask_discord_interactions import (
    ApplicationCommandType,
    Context,
    DiscordInteractionsBlueprint,
    Embed,
    Message,
    Modal,
    User,
)
from flask_discord_interactions.models.component import ActionRow, Button, Component, TextInput
from flask_discord_interactions.models.embed import Author, Field, Footer, Media
from i18n import t
from resources import companies, components, places, players, symbols
from utils import get_localizations

company_bp = DiscordInteractionsBlueprint()


def get_company_embed(user: User, player: players.Player, company: companies.Company) -> Embed:
    """Returns an embed with the company details"""
    founder = players.get(company.founder)
    company_embed = Embed(
        title=company.name,
        color=config.EMBED_COLOR,
        description=company.description,
        author=Author(name=t("company.author", name=player.name), icon_url=user.avatar_url),
        footer=Footer(text=t("company.founder", user=f"{founder.name}#{founder.discriminator}")),
        fields=[],
    )
    logo_is_discord_emoji = re.match(r"<(a?):\w*:(\d+)>", company.logo)
    if logo_is_discord_emoji:
        logo_animated = logo_is_discord_emoji.groups()[0] == "a"
        logo_id = logo_is_discord_emoji.groups()[1]
        company_embed.thumbnail = Media(
            url=f"https://cdn.discordapp.com/emojis/{logo_id}.{'gif' if logo_animated else 'png'}"
        )

    company_embed.fields.append(Field(name=t("company.hq_position"), value=str(company.hq_position)))
    company_embed.fields.append(Field(name=t("company.net_worth"), value=f"${company.net_worth:,}", inline=False))
    company_members = company.get_members()
    members = ""
    for member in company_members:
        members += f"{member} \n"
    company_embed.fields.append(
        Field(name=t("company.members", count=len(company_members)), value=members, inline=False)
    )
    return company_embed


@company_bp.custom_handler(custom_id="cancel_company_action")
def cancel(ctx: Context, player_id: str):
    """Cancel hire and fire"""
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    return Message(content=ctx.message.content, embeds=ctx.message.embeds, components=[], update=True)


@company_bp.custom_handler(custom_id="company_main")
def back(ctx: Context, player_id: str):
    """Shows the main buttons again"""
    player = players.get(ctx.author.id, check=player_id)
    company = companies.get(player.company)
    return Message(
        embed=get_company_embed(ctx.author, player, company),
        components=components.get_company_buttons(player, company),
        update=True,
    )


@company_bp.custom_handler(custom_id="company_found")
def found(ctx: Context, player_id: str):
    """Returns a modal to found a company"""
    player = players.get(ctx.author.id, check=player_id)
    if player.company is not None:
        return Message(t("company.founding.errors.already_existing"), ephemeral=True)
    if (
        int(player.position) in [int(p.position) for p in places.get_all()]
        or int(player.position) in [int(c.hq_position) for c in companies.get_all()]
        or int(player.position) == 0
    ):
        return Message(t("company.founding.errors.wrong_position"), ephemeral=True)

    return Modal(
        custom_id="modal_company_found",
        title=t("company.founding.modal.title"),
        components=[
            ActionRow(
                [
                    TextInput(
                        custom_id="modal_company_found_name",
                        label=t("company.founding.modal.name.label"),
                        placeholder=t("company.founding.modal.name.placeholder"),
                        min_length=3,
                        max_length=80,
                    )
                ]
            ),
            ActionRow(
                [
                    TextInput(
                        custom_id="modal_company_found_description",
                        label=t("company.founding.modal.description.label"),
                        placeholder=t("company.founding.modal.description.placeholder"),
                        style=2,
                        required=False,
                        max_length=1000,
                    )
                ]
            ),
        ],
    )


@company_bp.custom_handler(custom_id="modal_company_found")
def confirm_found(ctx: Context):
    """Modal handler for the company founding"""
    name = ctx.get_component("modal_company_found_name").value
    description = ctx.get_component("modal_company_found_description").value

    if companies.exists(name):
        return Message(t("company.founding.errors.doubled_name"), ephemeral=True)
    player = players.get(ctx.author.id)
    company = companies.Company(0, name, player.position, ctx.author.id, description=description)
    company_id = companies.insert(company)
    player.company = company_id
    return Message(
        embed=Embed(
            title=t("company.founding.success.title"),
            description=t("company.founding.success.body", logo=company.logo, name=company.name),
            color=config.EMBED_COLOR,
        ),
        components=[
            ActionRow(
                components=[Button(label=t("company.founding.success.cta"), custom_id=["company_main", player.id])]
            )
        ],
        update=True,
    )


@company_bp.custom_handler(custom_id="hire")
def hire(ctx: Context, user_id: str):
    """Button to hire a player"""
    player = players.get(ctx.author.id)
    invited_player = players.get(user_id)
    company = companies.get(player.company)
    if len(company.get_members()) > 24:
        return Message(t("company.hire.errors.too_many_members"), ephemeral=True)
    if invited_player.company is not None:
        return Message(t("company.hire.errors.already_member"), ephemeral=True)
    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(
                    style=2,
                    label=t("company.hire.decline", locale=ctx.guild_locale),
                    custom_id=["cancel_company_action", invited_player.id],
                ),
                Button(
                    style=3,
                    label=t("company.hire.accept", locale=ctx.guild_locale),
                    custom_id=["confirm_company_hire", company.id, invited_player.id],
                ),
            ]
        )
    ]
    return Message(
        t(
            "company.hire.message",
            hired_id=invited_player.id,
            employer=player.name,
            company=company.name,
            locale=ctx.guild_locale,
        ),
        components=confirm_buttons,
    )


@company_bp.custom_handler(custom_id="confirm_company_hire")
def confirm_hire(ctx: Context, company_id: int, player_id: str):
    """Confirm button the hired player has to click"""
    invited_player = players.get(ctx.author.id, check=player_id)

    company = companies.get(company_id)
    invited_player.company = company.id
    return Message(
        t("company.hire.success", player=invited_player, company=company.name),
        components=[],
        update=True,
    )


@company_bp.custom_handler("company_fire")
def fire(ctx: Context, player_id: str):
    """Select menu handler to fire a player"""
    player = players.get(ctx.author.id, check=player_id)
    fired_player = players.get(ctx.values[0])
    company = companies.get(player.company)
    if ctx.author.id == ctx.values[0]:
        # keeping this one here in case some of the select stuff fails
        return Message(t("company.fire.errors.self_firing"), ephemeral=True)
    if ctx.author.id != company.founder:
        return Message(t("company.update.errors.not_founder"), ephemeral=True)
    if fired_player.company != company.id:
        return Message(t("company.fire.errors.not_member"), ephemeral=True)

    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(style=2, label=t("cancel"), custom_id=["company_main", player.id]),
                Button(
                    style=4,
                    label=t("company.fire.cta"),
                    custom_id=["confirm_company_fire", company.name, player.id, fired_player.id],
                ),
            ]
        )
    ]
    return Message(t("company.fire.confirmation", player=fired_player), components=confirm_buttons, update=True)


@company_bp.custom_handler(custom_id="confirm_company_fire")
def confirm_fire(ctx: Context, company_name: str, player_id: str, fired_player_id: str):
    """Confirm button for the company owner"""
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    fired_player = players.get(fired_player_id)
    fired_player.company = None
    return Message(
        t("company.fire.success", player=fired_player, company=company_name),
        update=True,
        components=[
            ActionRow(components=[Button(label=t("back"), style=2, custom_id=["company_main", ctx.author.id])])
        ],
    )


@company_bp.custom_handler(custom_id="company_leave")
def leave(ctx: Context, player_id: str):
    """Leave your company"""
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(style=2, label=t("cancel"), custom_id=["company_main", ctx.author.id]),
                Button(style=4, label=t("company.leave.cta"), custom_id=["confirm_company_leave", ctx.author.id]),
            ]
        )
    ]
    return Message(t("company.leave.confirmation"), components=confirm_buttons, update=True)


@company_bp.custom_handler(custom_id="confirm_company_leave")
def confirm_leave(ctx: Context, player_id: str):
    """Confirm button to leave a company"""
    player = players.get(ctx.author.id, check=player_id)
    player.company = None
    return Message(
        t("company.leave.success", player_id=player.id),
        components=[ActionRow(components=[Button(label=t("back"), style=2, custom_id=["home", player.id])])],
        update=True,
    )


@company_bp.custom_handler(custom_id="company_update")
def company_update(ctx: Context, player_id: str):
    """A button handler that promts a select to select the options than should be changed"""
    player = players.get(ctx.author.id, check=player_id)
    company = companies.get(player.company)
    if ctx.author.id != company.founder:
        return Message("company.update.erros.not_founder", ephemeral=True)

    return Modal(
        custom_id="modal_company_update",
        title="Update your company",
        components=[
            ActionRow(
                [
                    TextInput(
                        custom_id="modal_company_update_name",
                        label=t("company.founding.modal.name.label"),
                        placeholder=t("company.founding.modal.name.placeholder"),
                        min_length=3,
                        max_length=80,
                        value=company.name,
                    )
                ]
            ),
            ActionRow(
                [
                    TextInput(
                        custom_id="modal_company_update_description",
                        label=t("company.founding.modal.description.label"),
                        placeholder=t("company.founding.modal.description.placeholder"),
                        style=2,
                        required=False,
                        value=company.description,
                        max_length=1000,
                    )
                ]
            ),
            ActionRow(
                [
                    TextInput(
                        custom_id="modal_company_update_logo",
                        label=t("company.update.modal.logo.label"),
                        placeholder=t("company.update.modal.logo.placeholder"),
                        min_length=1,
                        max_length=256,
                        value=company.logo,
                        required=False,
                    )
                ]
            ),
        ],
    )


@company_bp.custom_handler(custom_id="modal_company_update")
def update(ctx: Context):
    """Update a company's attributes"""
    player = players.get(ctx.author.id)
    company = companies.get(player.company)
    name: str = ctx.get_component("modal_company_update_name").value
    description: str = ctx.get_component("modal_company_update_description").value
    logo: str = ctx.get_component("modal_company_update_logo").value
    if name != company.name and companies.exists(name):
        return Message(t("company.founding.errors.doubled_name"), ephemeral=True)
    company.name = name
    company.description = description

    if logo == "":
        logo = "🏛️"
    if not re.match(
        # did I mention that I love regex?
        # match any emoji
        r"^[\u2600-\u26ff]|[\U0001f000-\U0001faff]|<a?:\w*:\d+>$",
        logo,
    ):
        return Message(t("company.update.errors.invalid_emoji"), ephemeral=True)
    company.logo = logo
    return Message(
        embed=get_company_embed(ctx.author, player, company),
        components=components.get_company_buttons(player, company),
        update=True,
    )


@company_bp.custom_handler(custom_id="manage_company")
def company_show(ctx: Context, player_id):
    """Manages your company."""

    player = players.get(ctx.author.id, check=player_id)
    try:
        company = companies.get(player.company)
    except companies.CompanyNotFound:
        buttons = [
            ActionRow(
                components=[Button(style=2, label=t("company.notfound.self.back"), custom_id=["home", player.id])]
            )
        ]
        if player.truck_id > 0:
            buttons[0].components.insert(
                0, Button(label=t("company.notfound.self.cta"), custom_id=["company_found", player.id])
            )

        return Message(
            t("company.notfound.self.message"),
            components=buttons,
            update=True,
        )
    return Message(
        embed=get_company_embed(ctx.author, player, company),
        components=components.get_company_buttons(player, company),
        update=True,
    )


@company_bp.command(
    name="Check company",
    type=ApplicationCommandType.USER,
    name_localizations=get_localizations("commands.company.name"),
)
def show_company(ctx: Context, user: User):
    """Context menu command to view a user's company"""
    player = players.get(user.id)
    origin_player = players.get(ctx.author.id)
    try:
        company = companies.get(player.company)
    except companies.CompanyNotFound:
        components = []
        if origin_player.company:
            company = companies.get(origin_player.company)
            if origin_player.id == company.founder and len(company.get_members()) < 25:
                components = [
                    ActionRow(
                        components=[
                            Button(
                                label=t("company.notfound.other.cta"),
                                custom_id=[
                                    "hire",
                                    user.id,
                                ],
                                emoji=symbols.parse_emoji(company.logo),
                            )
                        ]
                    )
                ]
        return Message(
            t("company.notfound.other.message", player=user.username),
            components=components,
            ephemeral=True,
        )
    return Message(embed=get_company_embed(user, player, company))
