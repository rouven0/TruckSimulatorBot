from resources.companies import CompanyNotFound
import traceback
from datetime import datetime
from math import floor
import logging

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, create_permission
from discord_slash.utils.manage_components import (
    create_button,
    create_actionrow,
)

import config
import resources.database as database
import resources.players as players
from resources.trucks import TruckNotFound


class System(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.start_time = datetime.now()
        self.owner_avatar = ""
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self):
        self.owner_avatar = (await self.bot.fetch_user(692796548282712074)).avatar_url

    async def get_info_embed(self) -> discord.Embed:
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.lighter_grey())
        info_embed.set_footer(
            text="Developer: r5#2253",
            icon_url=self.owner_avatar,
        )
        info_embed.set_thumbnail(url=self.bot.user.avatar_url)

        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours = floor(uptime.seconds / 3600)
        minutes = floor(uptime.seconds / 60) - hours * 60
        seconds = uptime.seconds - hours * 3600 - minutes * 60
        player_count = await players.get_count("players")
        driving_player_count = await players.get_count("driving_players")
        system_info = (
            f"```Uptime: {days}d {hours}h {minutes}m {seconds}s\n"
            f"Latency: {str(round(self.bot.latency * 1000))} ms\n"
            f"Registered Players: {player_count}\n"
            f"Driving Trucks: {driving_player_count}```"
        )
        info_embed.add_field(name="System information", value=system_info, inline=False)

        credits = (
            "<:lebogo:897861933418565652> LeBogo#3073 - _Testing helper_ - Contributed 2 lines of code\n"
            "<:panda:897860673898426462> FlyingPanda#0328 - _EPIC Artist_ - Drew almost all of the images you see (and had the idea of this bot)\n"
            "<:miri:897860673546117122> Miriel#0001 - _The brain_ - Gave a lot of great tips and constructive feedback"
        )
        info_embed.add_field(name="Credits", value=credits, inline=False)
        return info_embed

    @cog_ext.cog_slash()
    async def info(self, ctx) -> None:
        """
        System information and credits
        """
        await ctx.send(
            embed=await self.get_info_embed(),
            components=[
                create_actionrow(
                    create_button(
                        style=2, label="Refresh data", custom_id="refresh", emoji=self.bot.get_emoji(903581225149665290)
                    )
                )
            ],
        )

    @cog_ext.cog_component()
    async def refresh(self, ctx):
        await ctx.edit_origin(embed=await self.get_info_embed())
