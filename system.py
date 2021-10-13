import traceback
from driving import Driving
from datetime import datetime
from math import floor
import logging
import git

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_permission
from discord_slash.utils.manage_components import (
    create_button,
    create_actionrow,
    ComponentContext,
)

import api.players as players
from api.trucks import TruckNotFound


class System(commands.Cog):
    def __init__(self, bot: commands.Bot, driving_commands: Driving) -> None:
        self.bot = bot
        self.driving_commands = driving_commands
        self.start_time = datetime.now()
        self.repo = git.Repo()
        self.commit = self.repo.head.commit.hexsha[:7]
        self.summary = self.repo.head.commit.summary
        self.repo.close()
        super().__init__()

    @cog_ext.cog_slash()
    async def info(self, ctx) -> None:
        """
        System information and credits
        """
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.lighter_grey())
        info_embed.set_footer(
            text="Developer: r5#2253",
            icon_url="https://cdn.discordapp.com/avatars/692796548282712074/36f66390f3958970755416410237430a.png",
        )
        info_embed.set_thumbnail(url=self.bot.user.avatar_url)

        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours = floor(uptime.seconds / 3600)
        minutes = floor(uptime.seconds / 60) - hours * 60
        seconds = uptime.seconds - hours * 3600 - minutes * 60
        player_count = await players.get_count()
        system_info = (
            f"```Uptime: {days}d {hours}h {minutes}m {seconds}s\n"
            f"Latency: {str(round(self.bot.latency * 1000))} ms\n"
            f"Registered Players: {player_count}\n"
            f"Driving Trucks: {str(len(self.driving_commands.active_drives))}\n"
            f"Commit: {self.commit}\n"
            f"Commit Summary: {self.summary}```"
        )
        info_embed.add_field(name="System information", value=system_info, inline=False)

        credits = (
            "<:lebogo:897861933418565652> LeBogo#3073 - _Testing helper_ - Contributed 2 lines of code\n"
            "<:panda:897860673898426462> FlyingPanda#0328 - _EPIC Artist_ - Drew almost all of the images you see (and had the idea of this bot)\n"
            "<:miri:897860673546117122> Miriel#0001 - _The brain_ - Gave a lot of great tips and constructive feedback"
        )
        info_embed.add_field(name="Credits", value=credits, inline=False)
        await ctx.send(embed=info_embed)

    @cog_ext.cog_slash(
        guild_ids=[830928381100556338],
        default_permission=False,
        permissions={830928381100556338: [create_permission(692796548282712074, 2, True)]},
    )
    async def shutdown(self, ctx):
        await ctx.send(
            "Are you sure?",
            hidden=True,
            components=[
                create_actionrow(
                    create_button(style=3, label="Yes", custom_id="confirm_shutdown"),
                    create_button(style=4, label="No", custom_id="abort_shutdown"),
                )
            ],
        )

    @cog_ext.cog_component()
    async def confirm_shutdown(self, ctx: ComponentContext) -> None:
        await self.driving_commands.on_shutdown()
        await self.bot.change_presence(status=discord.Status.idle)
        await ctx.edit_origin(components=[])
        await ctx.send("Shutting down", hidden=True)
        logging.warning("Shutdown command is executed")
        await self.bot.close()

    @cog_ext.cog_component()
    async def abort_shutdown(self, ctx: ComponentContext):
        await ctx.edit_origin(content="Shutdown aborted", components=[])

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, error) -> None:
        if isinstance(error, players.NotEnoughMoney):
            await ctx.send("{} you don't have enough money to do this".format(ctx.author.mention))

        elif isinstance(error, players.PlayerNotRegistered):
            await ctx.send(
                "<@!{}> you are not registered yet! "
                "Try `/profile register` to get started".format(error.requested_id),
                hidden=True,
            )

        elif isinstance(error, TruckNotFound):
            await ctx.send("Truck not found", hidden=True)

        else:
            logging.error(f"{error.__class__.__name__} at /{ctx.command} executed by {ctx.author.name}: " + str(error))
            traceback.print_tb(error.__traceback__)
