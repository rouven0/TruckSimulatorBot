"Blueprint file containing all stat-related commands and handlers"
# pylint: disable=unused-argument, missing-function-docstring
from trucksimulator import config
from flask_discord_interactions import (
    ApplicationCommandType,
    Context,
    DiscordInteractionsBlueprint,
    Embed,
    Message,
    Component,
)
from flask_discord_interactions.models.component import (
    ActionRow,
    Button,
    SelectMenu,
    SelectMenuOption,
)
from flask_discord_interactions.models.embed import Author, Field, Footer, Media
from flask_discord_interactions.models.user import User
from i18n import t
from trucksimulator.resources import (
    assets,
    companies,
    components,
    levels,
    players,
    trucks,
)
from trucksimulator.utils import commatize, get_localizations

profile_bp = DiscordInteractionsBlueprint()


@profile_bp.command(
    name=t("commands.profile.name", locale=config.I18n.FALLBACK),
    name_localizations=get_localizations("commands.profile.name"),
    type=ApplicationCommandType.USER,
)
def profile(ctx: Context, user: User) -> Message:
    "Shows your profile."
    return Message(embed=get_profile_embed(user))


@profile_bp.custom_handler(custom_id="profile_register")
def register(ctx: Context, player_id: str):
    if ctx.author.id != player_id:
        return Message(update=True, deferred=True)
    if players.registered(ctx.author.id):
        return Message(update=True, deferred=True)
    with open(
        config.BASE_PATH + f"/messages/{ctx.locale if ctx.locale in config.I18n.AVAILABLE_LOCALES else config.I18n.FALLBACK}/welcome.md",
        "r",
        encoding="utf8",
    ) as welcome_file:
        welcome_embed = Embed(
            title=t("registering.title"),
            description=welcome_file.read(),
            color=config.EMBED_COLOR,
            author=Author(
                name=t("registering.welcome"),
                icon_url=config.SELF_AVATAR_URL,
            ),
            footer=Footer(text=t("registering.footer"), icon_url=ctx.author.avatar_url),
        )
    rules_embed = Embed(title=t("registering.rules.title"), color=config.EMBED_COLOR, fields=[])
    rules_embed.fields.append(
        Field(
            name=t("registering.rules.trading.title"),
            value=t("registering.rules.trading.content"),
        )
    )
    rules_embed.fields.append(
        Field(
            name=t("registering.rules.autotypers.title"),
            value=t("registering.rules.autotypers.content"),
        )
    )
    players.insert(
        players.Player(
            ctx.author.id,
            ctx.author.username,
            discriminator=ctx.author.discriminator,
            money=1000,
            gas=600,
        )
    )
    return Message(
        embeds=[welcome_embed, rules_embed],
        components=[
            ActionRow(
                components=[
                    Button(
                        label=t("registering.cta"),
                        custom_id=["initial_drive", ctx.author.id],
                        style=3,
                        emoji={"name": "default_truck", "id": 861674264737087519},
                    )
                ]
            )
        ],
        update=True,
    )


@profile_bp.custom_handler(custom_id="home")
def profile_home(ctx: Context, player_id):
    """Shows your profile."""
    player = players.get(ctx.author.id, check=player_id)
    return Message(
        embed=get_profile_embed(ctx.author),
        components=components.get_home_buttons(player),
        update=True,
    )


def get_profile_embed(user: User) -> Embed:
    player: players.Player = players.get(user.id)
    truck: trucks.Truck = trucks.get(player.truck_id)
    # Detect, when the player is renamed
    if player.name != user.username:
        player.name = user.username
    if player.discriminator != user.discriminator:
        player.discriminator = user.discriminator
    profile_embed = Embed(
        author=Author(name=t("profile.author", player=player.name)),
        thumbnail=Media(url=user.avatar_url),
        color=config.EMBED_COLOR,
        fields=[],
        image=Media(url=assets.get(f"/trucks/{player.truck_id}")),
        footer=Footer(text=t("profile.rank", rank=player.rank), icon_url=config.SELF_AVATAR_URL),
    )
    profile_embed.fields.append(
        Field(
            name=t("profile.level"),
            value=f"{player.level} ({player.xp:,}/{levels.get_next_xp(player.level):,} xp)",
            inline=False,
        )
    )
    profile_embed.fields.append(Field(name=t("profile.money"), value=f"${player.money:,}"))
    profile_embed.fields.append(
        Field(
            name=t("profile.miles"),
            value=f"{player.miles:,}\n" + t("profile.truck_miles", miles=commatize(player.truck_miles)),
            inline=False,
        )
    )
    profile_embed.fields.append(Field(name=t("profile.gas"), value=f"{player.gas:,} l", inline=False))
    profile_embed.fields.append(Field(name=t("profile.truck"), value=truck.name))
    if player.loaded_items:
        profile_embed.fields.append(
            Field(
                name=t("profile.load")
                + f" ({len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity})",
                value="".join([str(item) + "\n" for item in player.loaded_items]),
            )
        )

    try:
        company = companies.get(player.company)
        profile_embed.fields.append(Field(name=t("profile.company"), value=f"{company.logo} {company.name}"))
    except companies.CompanyNotFound:
        pass
    return profile_embed


@profile_bp.custom_handler(custom_id="top")
def top(ctx: Context, player_id) -> Message:
    "Presents the top players."
    return Message(
        embed=get_top_embed(),
        components=get_top_select(players.get(ctx.author.id, check=player_id)),
        update=True,
    )


@profile_bp.custom_handler(custom_id="top_select")
def top_select(ctx: Context, player_id) -> Message:
    "Handler for the toplist select"
    if ctx.author.id != player_id:
        raise players.WrongPlayer()
    return Message(
        embed=get_top_embed(ctx.values[0]),
        update=True,
        components=[Component.from_dict(c) for c in ctx.message.components],
    )


def get_top_embed(key="level") -> Embed:
    "Returns the top embed"
    top_players = players.get_top(key)
    top_body = ""
    count = 0
    top_embed = Embed(title=t("top.title"), color=config.EMBED_COLOR, fields=[])

    for player in top_players[0]:
        if key == "money":
            val = f"{player.money:,}"
        elif key == "miles":
            val = f"{player.miles:,}"
        else:
            val = f"{player.level:,} ({player.xp:,}/{levels.get_next_xp(player.level):,} xp)"
        count += 1
        top_body += f"**{count}**. {player} ~ {val}{top_players[1]}\n"
    top_embed.fields.append(Field(name=t(f"top.fields.{key}"), value=top_body))
    top_embed.footer = Footer(text=t("top.footer"), icon_url=config.SELF_AVATAR_URL)
    return top_embed


def get_top_select(player):
    "Returns the select appearing below /top"
    return [
        ActionRow(
            components=[
                SelectMenu(
                    custom_id=["top_select", player.id],
                    placeholder=t("top.select"),
                    options=[
                        SelectMenuOption(
                            label=t("top.keys.level"),
                            value="level",
                            emoji={"name": "🎉", "id": None},
                        ),
                        SelectMenuOption(
                            label=t("top.keys.money"),
                            value="money",
                            emoji={"name": "ts_money", "id": "868480873157242930"},
                        ),
                        SelectMenuOption(
                            label=t("top.keys.miles"),
                            value="miles",
                            emoji={"name": "default_truck", "id": "861674264737087519"},
                        ),
                    ],
                )
            ]
        ),
        ActionRow(components=[components.back_home(player.id)]),
    ]
