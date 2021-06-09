from os import getenv
from datetime import datetime
import asyncio
import logging
from discord.ext import commands
from dotenv import load_dotenv

import config
# from help import TruckSimulatorHelpCommand

from commands.system import System
from commands.driving import Driving
from commands.stats import Stats
from commands.economy import Economy
from commands.gambling import Gambling

load_dotenv('./.env')
BOT_TOKEN = getenv('BOT_TOKEN')
BOT_PREFIX = getenv('BOT_PREFIX').split(";")

def main():
    bot = commands.Bot(command_prefix=BOT_PREFIX,
                       # help_command=TruckSimulatorHelpCommand(),
                       help_command=commands.DefaultHelpCommand(),
                       case_insensitive=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt="%Y-%M-%d %H:%m:%S"))
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler("./logs/{}.log"
            .format(datetime.now().strftime("%Y-%m-%d_%H:%M")))
    file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(file_handler)

    driving_commands = Driving()
    bot.add_cog(System(bot, driving_commands))
    bot.add_cog(driving_commands)
    bot.add_cog(Stats())
    bot.add_cog(Economy())
    bot.add_cog(Gambling())
    loop = asyncio.get_event_loop()
    loop.create_task(driving_commands.check_drives())
    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
