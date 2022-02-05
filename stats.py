from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.command import ApplicationCommandType, CommandOptionType
from flask_discord_interactions.models.user import User
from flask_discord_interactions.models.embed import Author, Field, Footer, Media

import config
import resources.players as players
import resources.trucks as trucks
import resources.levels as levels
import resources.companies as companies

profile_bp = DiscordInteractionsBlueprint()


profile = profile_bp.command_group(name="profile", description="Show and manage your profile")


@profile.command(name="register", description="Register yourself to the Truck Simulator")
def register_profile(ctx) -> Message:
    welcome_file = open("./messages/welcome.md", "r")
    welcome_embed = Embed(
        title="Hey there, fellow Trucker,",
        description=welcome_file.read(),
        color=config.EMBED_COLOR,
        author=Author(
            name="Welcome to the Truck Simulator",
            icon_url=config.SELF_AVATAR_URL,
        ),
    )
    welcome_file.close()
    if not players.registered(ctx.author.id):
        players.insert(players.Player(int(ctx.author.id), ctx.author.username, money=1000))
        welcome_embed.footer = Footer(text="Your profile has been created")
    return Message(embed=welcome_embed)


@profile_bp.command(name="Check Profile", type=ApplicationCommandType.USER)
def show_profile_context(ctx, user: User) -> Message:
    return Message(embed=get_profile_embed(user))


@profile.command(
    name="show",
    description="Look at your profile",
    options=[
        {"name": "user", "description": "The user whose profile you want to look at", "type": CommandOptionType.USER}
    ],
)
def show_profile(ctx, user: User = None):
    return Message(embed=get_profile_embed(user if user is not None else ctx.author))


def get_profile_embed(user: User) -> Embed:
    player: players.Player = players.get(int(user.id))
    truck: trucks.Truck = trucks.get(player.truck_id)
    # Detect, when the player is renamed
    if player.name != user.username:
        players.update(player, name=user.username)
    profile_embed = Embed(
        author=Author(name=f"{player.name}'s profile"),
        thumbnail=Media(url=user.avatar_url),
        color=config.EMBED_COLOR,
        fields=[],
        image=Media(url=truck.image_url),
    )
    xp = "{:,}".format(player.xp)
    next_xp = "{:,}".format(levels.get_next_xp(player.level))
    money = "{:,}".format(player.money)
    miles = "{:,}".format(player.miles)
    truck_miles = "{:,}".format(player.truck_miles)
    profile_embed.fields.append(Field(name="Level", value=f"{player.level} ({xp}/{next_xp} xp)", inline=False))
    profile_embed.fields.append(Field(name="Money", value=f"${money}"))
    profile_embed.fields.append(
        Field(name="Miles driven", value=f"{miles}\n({truck_miles} with current truck)", inline=False)
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
    name="top",
    description="Have a look at several toplists",
    options=[
        {
            "name": "key",
            "description": "The list you desire to view",
            "type": CommandOptionType.STRING,
            "required": True,
            "choices": [
                {"name": "level", "value": "level"},
                {"name": "money", "value": "money"},
                {"name": "miles", "value": "miles"},
            ],
        }
    ],
)
def top(ctx, key) -> Message:
    top_players = players.get_top(key)
    top_body = ""
    count = 0
    top_embed = Embed(title="Truck Simulator top list", color=config.EMBED_COLOR, fields=[])

    for player in top_players[0]:
        if key == "money":
            val = "{:,}".format(player.money)
        elif key == "miles":
            val = "{:,}".format(player.miles)
        else:
            val = "{:,} ({}/{} xp)".format(player.level, player.xp, levels.get_next_xp(player.level))
            top_embed.footer = Footer(text="You can also sort by money and miles", icon_url=config.SELF_AVATAR_URL)
        count += 1
        top_body += "**{}**. {} ~ {}{}\n".format(count, player.name, val, top_players[1])
    top_embed.fields.append(Field(name=f"Top {key}", value=top_body))
    return Message(embed=top_embed)
