from time import time
from os import getenv
from datetime import datetime
from math import floor
from importlib import reload
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
# import help
import items
import players
import places

from commands.economy import Economy
from commands.stats import Stats
from commands.driving import Driving

load_dotenv('./.env')
BOT_TOKEN = getenv('BOT_TOKEN')
BOT_PREFIX = getenv('BOT_PREFIX').split(";")

def main():
    bot = commands.Bot(command_prefix=BOT_PREFIX,
                       help_command=commands.DefaultHelpCommand(),
                       case_insensitive=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(console_handler)

    file_handler = console_handler = logging.FileHandler("./logs/{}.log".format(datetime.now().strftime("%Y-%m-%d_%H:%M")))
    file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(file_handler)

    @bot.event
    async def on_ready():
        await bot.change_presence(status=discord.Status.online,
                                  activity=discord.Activity(
                                      type=discord.ActivityType.watching,
                                      name=str(len(bot.guilds)) + " Servers"))
        logging.info("Connected to Discord")
        logging.info(f'Loaded {len(places.get_all())} places')





    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def bing(ctx):
        answer = await ctx.channel.send("Bong")
        await ctx.channel.send(str(round((answer.created_at - ctx.message.created_at).total_seconds() * 1000)) + "ms")

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def info(ctx):
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.gold())

        uptime = datetime.now() - start_time
        days = uptime.days
        hours = floor(uptime.seconds / 3600)
        minutes = floor(uptime.seconds / 60) - hours * 60
        seconds = uptime.seconds - hours * 3600 - minutes * 60
        info_embed.add_field(name="Uptime",
                             value="{}d {}h {}m {}s".format(days, hours, minutes, seconds))
        info_embed.add_field(name="Latency", value=str(round(bot.latency, 2) * 1000) + " ms")
        info_embed.add_field(name="Registered Players", value=players.get_count())
        info_embed.add_field(name="Servers", value=len(bot.guilds))
        await ctx.channel.send(embed=info_embed)

    @bot.command()
    @commands.is_owner()
    async def adminctl(ctx, *args):
        if not args:
            await ctx.channel.send("Missing arguments")
            return
        if args[0] == "reloadplaces":
            reload(places)
            reload(items)
            await ctx.channel.send("Done")

        if args[0] == "shutdown":
            await driving_commands.on_shutdown()
            await bot.change_presence(status=discord.Status.idle)
            await ctx.channel.send("Shutting down")
            await bot.logout()

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.BotMissingPermissions):
            missing_permissions = '`'
            for permission in error.missing_perms:
                missing_permissions = missing_permissions + "\n" + permission
            await ctx.channel.send("I'm missing the following permissions:" + missing_permissions + '`')
        else:
            print(error)

    driving_commands = Driving()
    loop = asyncio.get_event_loop()
    loop.create_task(driving_commands.check_drives())
    start_time = datetime.now()
    bot.add_cog(Economy())
    bot.add_cog(Stats())
    bot.add_cog(driving_commands)
    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
