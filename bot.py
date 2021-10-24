from os import getenv
import sys
import asyncio
import logging
import discord
from discord.ext import commands
from discord_slash import SlashCommand

from dotenv import load_dotenv
import api.players as players

import config

load_dotenv("./.env")
BOT_TOKEN = getenv("BOT_TOKEN", default="")


def main():
    intents = discord.Intents.none()
    intents.guilds = True
    bot = commands.Bot(command_prefix="", help_command=None, case_insensitive=True, intents=intents)

    logger = logging.getLogger()

    if "--debug" in sys.argv:
        SlashCommand(bot, sync_commands=True, debug_guild=830928381100556338, sync_on_cog_reload=True)
        # logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.INFO)
    else:
        SlashCommand(bot, sync_commands=True, delete_from_unused_guilds=True, sync_on_cog_reload=True)
        logger.setLevel(logging.INFO)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(console_handler)

    for extension in config.EXTENSIONS:
        bot.load_extension(extension)
    asyncio.run(players.init())
    bot.run(BOT_TOKEN)
    asyncio.run(players.close())


if __name__ == "__main__":
    main()
