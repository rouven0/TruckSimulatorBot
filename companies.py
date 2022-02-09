from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed, User, ApplicationCommandType
from flask_discord_interactions.context import Context
from flask_discord_interactions.models import embed
from flask_discord_interactions.models.component import ActionRow, Button, Component, SelectMenu, SelectMenuOption
from flask_discord_interactions.models.embed import Author, Field, Footer, Media

import re

import config

import resources.players as players
import resources.places as places
import resources.companies as companies

company_bp = DiscordInteractionsBlueprint()

company_group = company_bp.command_group(name="company", description="View and manage your company")

# TODO rewrite this using modals and user selects (as soon as they are released)


@company_group.command(annotations={"name": "The name you give your company"})
def found(ctx, name: str):
    """Create a company"""
    if not re.match("^[a-zA-Z]", name):
        return "Bad name. Company names must start with a letter"

    player = players.get(ctx.author.id)
    if player.company is not None:
        return "You already have a company. You can't found another one!"
    if player.position in [p.position for p in places.get_all()] or player.position in [
        c.hq_position for c in companies.get_all()
    ]:
        return "You can't found a company on this position, please drive to an empty field."

    if companies.exists(name):
        return "A company with this make already exists, please choose another name"

    confirm_embed = Embed(
        title="Confirm your company creation",
        description=f"Please confirm that you want to found the company **{name}** as position {player.position}. "
        "This position is final, can not be changed and "
        "your company's logo will appear on this position on the map everyone can see.",
        color=config.EMBED_COLOR,
    )
    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(style=3, label="Confirm", custom_id=["confirm_company_found", name, ctx.author.id]),
                Button(style=4, label="Cancel", custom_id=["cancel_company_action", ctx.author.id]),
            ]
        )
    ]

    return Message(embed=confirm_embed, components=confirm_buttons)


@company_bp.custom_handler(custom_id="cancel_company_action")
def cancel(ctx, player_id: int):
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    return Message(content=ctx.message.content, embeds=ctx.message.embeds, components=[], update=True)


@company_bp.custom_handler(custom_id="confirm_company_found")
def confirm_found(ctx, name: str, player_id: int):
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    player = players.get(ctx.author.id)
    company = companies.Company(name, player.position, ctx.author.id)
    companies.insert(company)
    players.update(player, company=name)
    return Message(
        embed=Embed(
            title="Company creation successful",
            description=f"{company.logo} **{company.name}** has been created and placed in the market. "
            f"Your company's headquarters have been built at {company.hq_position}.\n"
            "To change your logo run `/company update`",
            color=config.EMBED_COLOR,
        ),
        components=[],
        update=True,
    )


@company_group.command(annotations={"user": "The player you want to hire"})
def hire(ctx, user: User):
    """Get a new player into your company"""
    player = players.get(int(ctx.author.id))
    invited_player = players.get(int(user.id))
    company = companies.get(player.company)
    if int(ctx.author.id) != company.founder:
        return "You are not the company founder!"
    if invited_player.company is not None:
        return f"**{invited_player.name}** already is member of a company."

    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(style=3, label="Confirm", custom_id=["confirm_company_hire", company.name, invited_player.id]),
                Button(style=4, label="Cancel", custom_id=["cancel_company_action", invited_player.id]),
            ]
        )
    ]
    return Message(
        f"<@{invited_player.id}> **{player.name}** wants to hire you for their company. "
        f"Please confirm that you want to work for {company.logo} **{company.name}**",
        components=confirm_buttons,
    )


@company_bp.custom_handler(custom_id="confirm_company_hire")
def confirm_hire(ctx, company: str, player_id: int):
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    invited_player = players.get(int(player_id))

    players.update(invited_player, company=company)
    return Message(
        f"It's official! **{invited_player.name}** is now a member of **{company}** <:PandaHappy:869202868555624478>",
        components=[],
        update=True,
    )


@company_group.command(annotations={"user": "The user you want to fire"})
def fire(ctx, user: User):
    """Remove a player from your company"""
    player = players.get(int(ctx.author.id))
    fired_player = players.get(int(user.id))
    company = companies.get(player.company)
    if ctx.author.id == user.id:
        return "You can't fire yourself!"
    if int(ctx.author.id) != company.founder:
        return "You are not the company founder!"
    if fired_player.company != company.name:
        return f"**{fired_player.name}** is not a member of your company."

    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(
                    style=3,
                    label="Confirm",
                    custom_id=["confirm_company_fire", company.name, player.id, fired_player.id],
                ),
                Button(style=4, label="Cancel", custom_id=["cancel_company_action", player.id]),
            ]
        )
    ]
    return Message(f"Are you sure you want to fire {fired_player.name}?", components=confirm_buttons)


@company_bp.custom_handler(custom_id="confirm_company_fire")
def confirm_fire(ctx, company: str, player_id: int, fired_player_id: int):
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    fired_player = players.get(int(fired_player_id))
    fired_player.remove_from_company()
    return f"**{fired_player.name}** was removed from **{company}**"


@company_group.command()
def leave(ctx):
    """Leave your company"""
    player = players.get(ctx.author.id)
    if player.company is None:
        return "You don't have company to leave!"
    company = companies.get(player.company)
    if ctx.author.id == company.founder:
        return "You can't leave the company you founded!"
    confirm_buttons: list[Component] = [
        ActionRow(
            components=[
                Button(style=3, label="Confirm", custom_id=["confirm_company_leave", ctx.author.id]),
                Button(style=4, label="Cancel", custom_id=["cancel_company_action", ctx.author.id]),
            ]
        )
    ]
    return Message("Are you sure that you want to leave your company?", components=confirm_buttons)


@company_bp.custom_handler(custom_id="confirm_company_leave")
def confirm_leave(ctx, player_id: int):
    if int(ctx.author.id) != player_id:
        return Message(deferred=True, update=True)
    player = players.get(player_id)
    player.remove_from_company()
    return Message(f"<@{player.id}> You left **{player.company}**", components=[], update=True)


@company_group.command(annotations={"name": "The new name", "logo": "Any emoji"})
def update(ctx, name: str = None, logo: str = None):
    """Change your company's logo"""
    player = players.get(int(ctx.author.id))
    company = companies.get(player.company)
    if int(ctx.author.id) != company.founder:
        return "You are not the company founder!"
    if name:
        if companies.exists(name):
            return "A company with this make already exists, please choose another name"
        else:
            companies.update(company, name=name)
            return f"Done. Your company was renamed to {name}"

    if logo:
        if re.match(
            # did I mention that I love regex?
            # match any emoji
            r"^([\u2600-\u26ff]|[\U0001f000-\U0001faff])|<a*:\w*:\d+>$",
            logo,
        ):
            companies.update(company, logo=logo)
            return f"Done. Your company logo was set to {logo} Please note that your logo can be reset at any time if it is found not working or inappropriate"
        else:
            return "That's not an emoji"


def get_company_embed(user, player, company) -> Embed:
    founder = players.get(company.founder)
    logo_id = company.logo[company.logo.find(":", 2) + 1 : company.logo.find(">")]
    company_embed = Embed(
        title=company.name,
        color=config.EMBED_COLOR,
        author=Author(name=f"{player.name}'s company", icon_url=user.avatar_url),
        footer=Footer(text=f"Founded by {founder.name}"),
        thumbnail=Media(url=f"https://cdn.discordapp.com/emojis/{logo_id}.png"),
        fields=[],
    )
    company_embed.fields.append(Field(name="Headquarters position", value=str(company.hq_position)))
    company_embed.fields.append(Field(name="Net worth", value=f"${company.net_worth}", inline=False))
    members = ""
    for member in company.get_members():
        members += f"{member.name} \n"
    company_embed.fields.append(Field(name="Members", value=members, inline=False))
    return company_embed


@company_group.command()
def show(ctx, user: User = None):
    """Show details about your company"""
    if user is not None:
        target_user = user
    else:
        target_user = ctx.author
    player = players.get(int(target_user.id))
    try:
        company = companies.get(player.company)
    except companies.CompanyNotFound:
        begin = "You are " if user is None else f"**{user.username}** is "
        return begin + "not member of a company at the moment"
    return Message(embed=get_company_embed(target_user, player, company))


@company_bp.command(name="Show company", type=ApplicationCommandType.USER)
def show_company(ctx, user: User):
    player = players.get(int(user.id))
    try:
        company = companies.get(player.company)
    except companies.CompanyNotFound:
        return f"**{user.username}** is not member of a company at the moment"
    return Message(embed=get_company_embed(user, player, company))
