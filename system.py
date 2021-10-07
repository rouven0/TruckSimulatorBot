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

    @cog_ext.cog_subcommand(base="system")
    async def info(self, ctx) -> None:
        """
        System information (mostly useful for the dev)
        """
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.lighter_grey())
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours = floor(uptime.seconds / 3600)
        minutes = floor(uptime.seconds / 60) - hours * 60
        seconds = uptime.seconds - hours * 3600 - minutes * 60
        info_embed.add_field(name="Uptime", value="{}d {}h {}m {}s".format(days, hours, minutes, seconds))
        info_embed.add_field(name="Latency", value=str(round(self.bot.latency * 1000)) + " ms")
        info_embed.add_field(name="Registered Players", value=str(await players.get_count()))
        info_embed.add_field(name="Driving Trucks", value=str(len(self.driving_commands.active_drives)))
        info_embed.add_field(name="Commit", value=self.commit)
        info_embed.add_field(name="Commit Summary", value=self.summary)
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
