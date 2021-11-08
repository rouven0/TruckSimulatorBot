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
import api.database as database
import api.players as players
from api.trucks import TruckNotFound


class System(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.start_time = datetime.now()
        super().__init__()

    async def get_info_embed(self) -> discord.Embed:
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

    @cog_ext.cog_subcommand(
        base="blacklist",
        guild_ids=[839580174282260510],
        base_default_permission=False,
        base_permissions={839580174282260510: [create_permission(692796548282712074, 2, True)]},
    )
    async def add(self, ctx, user_id, reason: str) -> None:
        user_id = int(user_id)
        try:
            player = await players.get(user_id)
            await ctx.send(
                embed=discord.Embed(
                    description=f":white_check_mark: **{player.name}** got blacklisted",
                    colour=discord.Colour.lighter_grey(),
                )
            )
            await players.update(player, name=reason, xp=-1)
        except players.PlayerBlacklisted:
            await ctx.send("Player already blacklisted")

    @cog_ext.cog_subcommand(
        base="blacklist",
        guild_ids=[839580174282260510],
        base_default_permission=False,
        base_permissions={839580174282260510: [create_permission(692796548282712074, 2, True)]},
    )
    async def remove(self, ctx, user_id) -> None:
        user_id = int(user_id)
        try:
            await players.get(user_id)
            await ctx.send("Player not on blacklist")
        except players.PlayerBlacklisted:
            user = await self.bot.fetch_user(user_id)
            player = players.Player(user_id, user.name)
            await players.update(player, xp=0, name=user.name)
            await ctx.send(
                embed=discord.Embed(
                    description=f":white_check_mark: **{player.name}** got removed from the blacklist",
                    colour=discord.Colour.lighter_grey(),
                )
            )

    @cog_ext.cog_subcommand(
        base="extension",
        options=[
            create_option(
                name="extension",
                description="Extension to be reloaded",
                option_type=3,
                choices=config.EXTENSIONS,
                required=True,
            )
        ],
        guild_ids=[839580174282260510],
        base_default_permission=False,
        base_permissions={839580174282260510: [create_permission(692796548282712074, 2, True)]},
    )
    async def reload(self, ctx, extension: str) -> None:
        """
        Reload an extension
        """
        self.bot.reload_extension(extension)
        await ctx.send(f"Reloaded {extension}")

    @cog_ext.cog_subcommand(
        base="execute",
        guild_ids=[839580174282260510],
        base_default_permission=False,
        base_permissions={839580174282260510: [create_permission(692796548282712074, 2, True)]},
    )
    @commands.is_owner()
    async def sql(self, ctx, query: str):
        await ctx.defer()
        try:
            cur = await database.con.execute(query)
            await database.con.commit()
            if cur.rowcount != -1:
                await ctx.send(f"`Done. {cur.rowcount} row(s) affected`")
            else:
                await ctx.send(f"```\n{await cur.fetchall()}```")
            await cur.close()
        except Exception as e:
            await ctx.send("Error: " + str(e))

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, error) -> None:
        if isinstance(error, players.NotEnoughMoney):
            await ctx.send("{} you don't have enough money to do this".format(ctx.author.mention))

        elif isinstance(error, players.PlayerNotRegistered):
            await ctx.send(
                f"<@!{error.requested_id}> you are not registered yet! Try `/profile register` to get started",
                hidden=True,
            )

        elif isinstance(error, players.PlayerBlacklisted):
            await ctx.send(
                f"<@!{error.requested_id}> you are blacklisted for reason: {error.reason}",
                hidden=True,
            )

        elif isinstance(error, TruckNotFound):
            await ctx.send("Truck not found", hidden=True)

        else:
            logging.error(f"{error.__class__.__name__} at /{ctx.command} executed by {ctx.author.name}: " + str(error))
            await ctx.send(
                f"Looks like we got an error here. ```{error.__class__.__name__}: {error}``` If this occurs multiple times feel free to report it in the support server"
            )
            traceback.print_tb(error.__traceback__)

    @commands.Cog.listener()
    async def on_component_callback_error(self, ctx, error) -> None:
        if isinstance(error, players.NotDriving):
            await ctx.defer(ignore=True)
        else:
            logging.error(f"{error.__class__.__name__} on a component: " + str(error))
            traceback.print_tb(error.__traceback__)


def setup(bot):
    bot.add_cog(System(bot))
