from os import getenv
import sys
import asyncio
import logging
import discord
from discord.ext import commands
from discord_slash import SlashCommand

from dotenv import load_dotenv
import resources.database as database

import config

load_dotenv("./.env")
BOT_TOKEN = getenv("BOT_TOKEN", default="")


def main():
    intents = discord.Intents.none()
    intents.guilds = True
    bot = commands.Bot(command_prefix="", help_command=None, case_insensitive=True, intents=intents)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if "--full" in sys.argv:
        logger.setLevel(logging.DEBUG)

    if "--debug" in sys.argv:
        SlashCommand(bot, sync_commands=True, debug_guild=830928381100556338, sync_on_cog_reload=True)
    else:
        SlashCommand(bot, sync_commands=True, delete_from_unused_guilds=True)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(console_handler)

    for extension in config.EXTENSIONS:
        bot.load_extension(extension)
    asyncio.run(database.init())
    bot.run(BOT_TOKEN)
    asyncio.run(database.close())


if __name__ == "__main__":
    main()
