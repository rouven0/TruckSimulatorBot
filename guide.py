# pylint: disable=unused-argument
from os import listdir
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.option import CommandOptionType
from flask_discord_interactions.models.embed import Field, Author, Media
from flask_discord_interactions.models.autocomplete import Autocomplete

import config

from resources import items
from resources import players
from resources import assets
from resources import places

guide_bp = DiscordInteractionsBlueprint()


@guide_bp.command(
    options=[
        {
            "name": "item",
            "description": "The item you want to view",
            "type": CommandOptionType.STRING,
            "choices": [{"name": i.name, "value": i.name} for i in items.get_all()],
            "required": True,
        }
    ]
)
def iteminfo(ctx, item: str) -> Message:
    """Prints some information about a specific item"""
    requested_item = items.get(item)
    item_embed = Embed(
        title=f"Item info for {requested_item.name}",
        description=requested_item.description,
        color=config.EMBED_COLOR,
        thumbnail=Media(url=f"https://cdn.discordapp.com/emojis/{requested_item.emoji}.webp"),
        fields=[],
    )
    for place in places.get_all():
        if place.produced_item == item:
            item_embed.fields.append(Field(name="Found at", value=place.name))
    return Message(embed=item_embed)


@guide_bp.command(annotations={"place": "The place you want to view"})
def placeinfo(ctx, place: Autocomplete(str)) -> Message:
    """Prints some information about a specific place"""
    player = players.get(ctx.author.id)
    try:
        queried_place = places.get(place)
    except ValueError:
        return Message("Place not found")
    position_embed = Embed(
        title="What is here?",
        description=queried_place.name,
        color=config.EMBED_COLOR,
        fields=[Field(name="Position", value=str(queried_place.position))],
    )
    if queried_place.image_url_default is not None:
        position_embed.fields.append(Field(name="Produced item", value=str(items.get(queried_place.produced_item))))
        position_embed.image = Media(url=assets.get_place_image(player, queried_place))
    if queried_place.accepted_item:
        position_embed.fields.append(Field(name="Accepted item", value=str(items.get(queried_place.accepted_item))))

    return Message(embed=position_embed)


@placeinfo.autocomplete()
def place_autocomplete(ctx, place):
    """Returns matching choices for a place name"""
    return places.get_matching_options(place.value)


@guide_bp.command(
    options=[
        {
            "name": "topic",
            "description": "The topic you want to read about",
            "type": CommandOptionType.STRING,
            "choices": [{"name": f[: f.find(".")], "value": f[: f.find(".")]} for f in listdir("./guide")],
        }
    ],
)
def guide(ctx, topic: str = "introduction") -> Message:
    """A nice little guide that helps you understand this bot"""
    with open(f"./guide/{topic}.md", "r", encoding="utf8") as guide_file:
        topic = str.lower(topic)
        image_url = guide_file.readline()
        guide_embed = Embed(
            title=f"{str.upper(topic[0])}{topic[1:]}",
            description=guide_file.read(),
            color=config.EMBED_COLOR,
            author=Author(name="Truck Simulator Guide", icon_url=config.SELF_AVATAR_URL),
        )
        if image_url.startswith("https"):
            guide_embed.image = Media(url=image_url)
        else:
            guide_embed.description = image_url + guide_embed.description
    return Message(embed=guide_embed)
