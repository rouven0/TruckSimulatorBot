from os import getenv
import sys
import asyncio
import logging
from datetime import datetime
from importlib import reload
from types import ModuleType
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv


import config
# from help import TruckSimulatorHelpCommand

from ts_commands.system import System
from ts_commands.driving import Driving
from ts_commands.stats import Stats
from ts_commands.economy import Economy
from ts_commands.gambling import Gambling
from ts_commands.misc import Misc

load_dotenv('./.env')
BOT_TOKEN = getenv('BOT_TOKEN')
BOT_PREFIX = getenv('BOT_PREFIX').split(";")


def main():
    bot = commands.AutoShardedBot(shard_count=1, command_prefix=BOT_PREFIX,
                                  # help_command=TruckSimulatorHelpCommand(),
                                  help_command=commands.DefaultHelpCommand(),
                                  case_insensitive=True)

    def reloadcommands(module):
        """
        Recursively reload modules.
        """
        target_modules=["assets", "config", "help", "items", "jobs", "places", "players", "symbols"]
        reload(module)
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if isinstance(attribute, ModuleType) and attribute.__name__ in target_modules:
                reloadcommands(attribute)
                logging.info("Reloaded %s in %s", attribute.__name__, module.__name__, attribute.__name__, module.__name__)

    @bot.command(hidden=True)
    @commands.is_owner()
    async def ts_reload(ctx):
        logging.warning("Reload command is invoked")
        bot.remove_cog("System")
        bot.remove_cog("Driving")
        bot.remove_cog("Stats")
        bot.remove_cog("Economy")
        bot.remove_cog("Gambling")
        bot.remove_cog("Misc")
        logging.warning("Unloaded all cogs")
        reload(config)
        reloadcommands(sys.modules["ts_commands.system"])
        reloadcommands(sys.modules["ts_commands.driving"])
        reloadcommands(sys.modules["ts_commands.stats"])
        reloadcommands(sys.modules["ts_commands.economy"])
        reloadcommands(sys.modules["ts_commands.gambling"])
        reloadcommands(sys.modules["ts_commands.misc"])
        driving_commands = Driving(bot)
        bot.add_cog(System(bot, driving_commands))
        bot.add_cog(driving_commands)
        bot.add_cog(Stats(bot))
        bot.add_cog(Economy())
        bot.add_cog(Gambling())
        bot.add_cog(Misc())
        logging.info("Reloaded all cogs")
        await ctx.channel.send("Done.")

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
    bot.add_cog(System(bot, driving_commands))
    bot.add_cog(driving_commands)
    bot.add_cog(Stats(bot))
    bot.add_cog(Economy())
    bot.add_cog(Gambling())
    bot.add_cog(Misc())
    loop = asyncio.get_event_loop()
    loop.create_task(driving_commands.check_drives())
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()
