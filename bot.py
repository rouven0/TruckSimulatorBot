from os import getenv
import sys
import asyncio
import logging
from datetime import datetime
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv


import config
from help import TruckSimulatorHelpCommand

from commands.system import System
from commands.driving import Driving
from commands.stats import Stats
from commands.economy import Economy
from commands.gambling import Gambling
from commands.misc import Misc

load_dotenv('./.env')
BOT_TOKEN = getenv('BOT_TOKEN')
BOT_PREFIX = getenv('BOT_PREFIX').split(";")
INGAME_NEWS_CHANNEL_ID = int(getenv('INGAME_NEWS_CHANNEL_ID'))


def main():
    bot = commands.Bot(command_prefix=BOT_PREFIX,
                       help_command=TruckSimulatorHelpCommand(),
                       case_insensitive=True)

    DiscordComponents(bot)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(console_handler)

    if "--enable-log-file" in sys.argv:
        file_handler = logging.FileHandler("./logs/{}.log"
               .format(datetime.now().strftime("%Y-%m-%d_%H:%M")))
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        logger.addHandler(file_handler)
        logging.info("Logging into file is enabled")

    driving_commands = Driving(bot)
    economy_commands = Economy(bot, (INGAME_NEWS_CHANNEL_ID), driving_commands)
    bot.add_cog(System(bot, driving_commands))
    bot.add_cog(driving_commands)
    bot.add_cog(Stats(bot))
    bot.add_cog(economy_commands)
    bot.add_cog(Gambling())
    bot.add_cog(Misc())
    loop = asyncio.get_event_loop()
    loop.create_task(driving_commands.check_drives())
    loop.create_task(economy_commands.daily_gas_prices())
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()
