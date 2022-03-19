"Blueprint file containing all stat-related commands and handlers"
# pylint: disable=unused-argument, missing-function-docstring
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.command import ApplicationCommandType
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.option import CommandOptionType
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field, Footer, Media

import config
from resources import players
from resources import trucks
from resources import levels
from resources import companies

profile_bp = DiscordInteractionsBlueprint()


@profile_bp.command(name="Check profile", type=ApplicationCommandType.USER)
def show_profile_context(ctx, user: User) -> Message:
    return Message(embed=get_profile_embed(user), ephemeral=True)


@profile_bp.custom_handler(custom_id="profile_register")
def register(ctx):
    with open("./messages/welcome.md", "r", encoding="utf8") as welcome_file:
        welcome_embed = Embed(
            title="Hey there, fellow Trucker,",
            description=welcome_file.read(),
            color=config.EMBED_COLOR,
            author=Author(
                name="Welcome to the Truck Simulator",
                icon_url=config.SELF_AVATAR_URL,
            ),
            footer=Footer(text="Your profile has been created", icon_url=ctx.author.avatar_url),
        )
    rules_embed = Embed(title="Rules", color=config.EMBED_COLOR, fields=[])
    rules_embed.fields.append(
        Field(
            name="Trading ingame currency for real money",
            value="Not only that it is pretty stupid to trade real world's money in exchange of a number "
            "somewhere in a random database it will also get you banned from this bot.",
            inline=False,
        )
    )
    rules_embed.fields.append(
        Field(
            name="Autotypers",
            value="Don't even try, it's just wasted work only to get you blacklisted.",
        )
    )
    players.insert(
        players.Player(ctx.author.id, ctx.author.username, discriminator=ctx.author.discriminator, money=1000, gas=600)
    )
    return Message(
        embeds=[welcome_embed, rules_embed],
        components=[
            ActionRow(
                components=[
                    Button(
                        label="Let's go!",
                        custom_id=["initial_drive", ctx.author.id],
                        style=3,
                        emoji={"name": "default_truck", "id": 861674264737087519},
                    )
                ]
            )
        ],
    )


@profile_bp.command(annotations={"user": "A user you want to view."})
def profile(ctx, user: User = None):
    """Shows your profile."""
    return Message(embed=get_profile_embed(user if user is not None else ctx.author))


def get_profile_embed(user: User) -> Embed:
    player: players.Player = players.get(user.id)
    truck: trucks.Truck = trucks.get(player.truck_id)
    # Detect, when the player is renamed
    if player.name != user.username:
        players.update(player, name=user.username)
    if player.discriminator != user.discriminator:
        players.update(player, discriminator=user.discriminator)
    profile_embed = Embed(
        author=Author(name=f"{player.name}'s profile"),
        thumbnail=Media(url=user.avatar_url),
        color=config.EMBED_COLOR,
        fields=[],
        image=Media(url=truck.image_url),
    )
    profile_embed.fields.append(
        Field(
            name="Level", value=f"{player.level} ({player.xp:,}/{levels.get_next_xp(player.level):,} xp)", inline=False
        )
    )
    profile_embed.fields.append(Field(name="Money", value=f"${player.money:,}"))
    profile_embed.fields.append(
        Field(name="Miles driven", value=f"{player.miles:,}\n({player.truck_miles:,} with current truck)", inline=False)
    )
    profile_embed.fields.append(Field(name="Gas left", value=f"{player.gas} l", inline=False))
    profile_embed.fields.append(Field(name="Current truck", value=truck.name))

    try:
        company = companies.get(player.company)
        profile_embed.fields.append(Field(name="Company", value=f"{company.logo} {company.name}"))
    except companies.CompanyNotFound:
        pass
    return profile_embed


@profile_bp.command(
    options=[
        {
            "name": "key",
            "description": "The list you desire to view.",
            "type": CommandOptionType.STRING,
            "choices": [
                {"name": "level", "value": "level"},
                {"name": "money", "value": "money"},
                {"name": "miles", "value": "miles"},
            ],
        }
    ],
)
def top(ctx, key="level") -> Message:
    """Presents the top players."""
    top_players = players.get_top(key)
    top_body = ""
    count = 0
    top_embed = Embed(title="Truck Simulator top list", color=config.EMBED_COLOR, fields=[])

    for player in top_players[0]:
        if key == "money":
            val = f"{player.money:,}"
        elif key == "miles":
            val = f"{player.miles:,}"
        else:
            val = f"{player.level:,} ({player.xp:,}/{levels.get_next_xp(player.level):,} xp)"
            top_embed.footer = Footer(text="You can also sort by money and miles", icon_url=config.SELF_AVATAR_URL)
        count += 1
        top_body += f"**{count}**. {player} ~ {val}{top_players[1]}\n"
    top_embed.fields.append(Field(name=f"Top {key}", value=top_body))
    return Message(embed=top_embed)
