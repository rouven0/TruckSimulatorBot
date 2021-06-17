from datetime import datetime
from math import floor
import logging
import git

import discord
from discord.ext import commands

import players


class System(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot, driving_commands):
        self.bot = bot
        self.driving_commands = driving_commands
        self.start_time = datetime.now()
        self.repo = git.Repo()
        self.commit=self.repo.head.commit.hexsha[:7]

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(status=discord.Status.online,
                                       activity=discord.Activity(
                                           type=discord.ActivityType.watching,
                                           name="t.help on " + str(len(self.bot.guilds)) + " Servers"))
        logging.info("Connected to Discord")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot.change_presence(status=discord.Status.online,
                                       activity=discord.Activity(
                                           type=discord.ActivityType.watching,
                                           name="t.help on " + str(len(self.bot.guilds)) + " Servers"))
        logging.info("Joined {} [{}]".format(guild.name, guild.id))

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def bing(self, ctx):
        answer = await ctx.channel.send("Bong")
        await ctx.channel.send(str(round((answer.created_at - ctx.message.created_at).total_seconds() * 1000)) + "ms")

    @commands.command()
    async def info(self, ctx):
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.gold())
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours = floor(uptime.seconds / 3600)
        minutes = floor(uptime.seconds / 60) - hours * 60
        seconds = uptime.seconds - hours * 3600 - minutes * 60
        info_embed.add_field(name="Uptime",
                             value="{}d {}h {}m {}s".format(days, hours, minutes, seconds))
        info_embed.add_field(name="Latency", value=str(round(self.bot.latency, 2) * 1000) + " ms")
        info_embed.add_field(name="Registered Players", value=players.get_count())
        info_embed.add_field(name="Servers", value=len(self.bot.guilds))
        info_embed.add_field(name="Driving Trucks", value=len(self.driving_commands.active_drives))
        info_embed.add_field(name="Branch", value=self.repo.active_branch.name)
        info_embed.add_field(name="Commit", value=self.commit)
        await ctx.channel.send(embed=info_embed)

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        await self.driving_commands.on_shutdown()
        await ctx.channel.send("Shutting down")
        logging.warning("Shutdown command is executed")
        await self.bot.close()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: commands.CommandError):
        if isinstance(error, commands.errors.BotMissingPermissions):
            missing_permissions = '`'
            for permission in error.missing_perms:
                missing_permissions = missing_permissions + "\n" + permission
            await ctx.channel.send("I'm missing the following permissions:" + missing_permissions + '`')
        elif isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.original, players.PlayerNotRegistered):
                await ctx.channel.send(
                    "<@!{}> you are not registered yet! "
                    "Try `t.register` to get started".format(error.original.requested_id))
        else:
            logging.error(error)
