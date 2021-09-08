from os import getenv
import sys
import asyncio
import logging
from datetime import datetime
import discord
from discord.ext import commands
from discord.ext import tasks
from discord_slash import SlashCommand

import topgg

from dotenv import load_dotenv
import players

import config

from commands.system import System
from commands.driving import Driving
from commands.stats import Stats
from commands.economy import Economy
from commands.gambling import Gambling
from commands.misc import Misc
from commands.trucks import Trucks

load_dotenv("./.env")
BOT_TOKEN = getenv("BOT_TOKEN", default="")
DBL_TOKEN = getenv("DBL_TOKEN", default="")
INGAME_NEWS_CHANNEL_ID = int(getenv("INGAME_NEWS_CHANNEL_ID", default=0))


def main():
    bot = commands.Bot(command_prefix=["t.", "T."], help_command=None, case_insensitive=True)

    bot.topggpy = topgg.DBLClient(bot, DBL_TOKEN)
    bot.topgg_webhook = topgg.WebhookManager(bot).dbl_webhook("/dblwebhook", "TruckSimulator")
    bot.topgg_webhook.run(5000)

    SlashCommand(bot, sync_commands=True)
    logger = logging.getLogger()

    if "--debug" in sys.argv:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(console_handler)

    if "--enable-log-file" in sys.argv:
        file_handler = logging.FileHandler("./logs/{}.log".format(datetime.now().strftime("%Y-%m-%d_%H:%M")))
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)
        logging.info("Logging into file is enabled")

    driving_commands = Driving(bot)
    economy_commands = Economy(bot, INGAME_NEWS_CHANNEL_ID, driving_commands)
    bot.add_cog(System(bot, driving_commands))
    bot.add_cog(driving_commands)
    bot.add_cog(Stats(bot))
    bot.add_cog(economy_commands)
    bot.add_cog(Gambling(bot))
    bot.add_cog(Misc())
    bot.add_cog(Trucks(bot, driving_commands))

    @bot.command(aliases=["truck", "drive", "job"])
    async def help(ctx):
        await ctx.channel.send(
            embed=discord.Embed(
                title="Hey there fellow Trucker",
                description="This bot has switched to slash commands. "
                "Just type / and you will see a list of all available commands. "
                "If you don't see them, make sure you have the permission to use application commands and your server "
                "admin granted the bot the slash commands scope using [this link]"
                "(https://discord.com/api/oauth2/authorize?client_id=831052837353816066&permissions=3072&scope=bot%20applications.commands).",
                colour=discord.Colour.gold(),
            )
        )

    @tasks.loop(minutes=120)
    async def update_stats():
        """This function runs every 30 minutes to automatically update your server count."""
        try:
            await bot.topggpy.post_guild_count()
            logging.info(f"Posted server count ({bot.topggpy.guild_count})")
        except Exception as e:
            logging.error(f"Failed to post server count\n{e.__class__.__name__}: {e}")

    if "--post-server-count" in sys.argv:
        update_stats.start()

    @bot.event
    async def on_dbl_vote(data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        if data["type"] == "test":
            return bot.dispatch("dbl_test", data)
        logging.info(f"Received a vote:\n{data}")

    asyncio.run(players.init())
    bot.run(BOT_TOKEN)
    asyncio.run(players.close())


if __name__ == "__main__":
    main()
