"""
This module contains a Cog for all the help-related commands
"""

from os import listdir
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

import api.items as items
import api.places as places


class Guide(commands.Cog):
    """
    A set of helpful commands
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @cog_ext.cog_slash(
        options=[
            create_option(
                name="item",
                description="The item you want to view",
                option_type=3,
                choices=[i.name for i in items.get_all()],
                required=True,
            )
        ]
    )
    async def iteminfo(self, ctx, item: str) -> None:
        """
        Prints some information about a specific item
        """
        requested_item = items.get(item)
        item_embed = discord.Embed(
            title=f"Item info for {requested_item.name}",
            description=requested_item.description,
            colour=discord.Colour.gold(),
        )
        for place in places.get_all():
            if place.produced_item == item:
                item_embed.add_field(name="Found at", value=place.name)
        await ctx.send(embed=item_embed)

    @cog_ext.cog_slash(
        options=[
            create_option(
                name="topic",
                description="The topic you want to read about",
                option_type=3,
                choices=[f[: f.find(".")] for f in listdir("./guide")],
                required=True,
            )
        ],
    )
    async def guide(self, ctx, topic: str) -> None:
        """
        A nice little guide that helps you understand this bot
        """
        if topic is None:
            topic = "guide"
        topic = str.lower(topic)
        try:
            guide_file = open(f"./guide/{topic}.md", "r")
        except FileNotFoundError:
            await ctx.send("Requested topic not found")
            return
        guide_embed = discord.Embed(
            title=f"{str.upper(topic[0])}{topic[1:]}", description=guide_file.read(), colour=discord.Colour.gold()
        )
        guide_embed.set_author(name="Truck Simulator Guide", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=guide_embed)
        guide_file.close()
