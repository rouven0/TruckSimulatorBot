from discord.ext import commands

class TruckSimulatorHelpCommand(commands.HelpCommand):
    def __init__(self):
        self.command_attrs=dict(hidden=True)
