from os import getenv
import sys
import asyncio
import logging
from datetime import datetime
from discord.ext import commands
from discord.ext import tasks
from discord_components import DiscordComponents
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

load_dotenv('./.env')
BOT_TOKEN = getenv('BOT_TOKEN', default="")
BOT_PREFIX = getenv('BOT_PREFIX', default="").split(";")
DBL_TOKEN = getenv('DBL_TOKEN', default="")
INGAME_NEWS_CHANNEL_ID = int(getenv('INGAME_NEWS_CHANNEL_ID', default=0))


def main():
    bot = commands.Bot(command_prefix=BOT_PREFIX,
                       help_command=None(),
                       case_insensitive=True)

    bot.topggpy = topgg.DBLClient(bot, DBL_TOKEN)

    DiscordComponents(bot)
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
        file_handler = logging.FileHandler("./logs/{}.log"
                                           .format(datetime.now().strftime("%Y-%m-%d_%H:%M")))
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

    asyncio.run(players.init())
    bot.run(BOT_TOKEN)
    asyncio.run(players.close())


if __name__ == '__main__':
    main()
