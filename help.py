import discord
from discord.ext import commands


class TruckSimulatorHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        help_embed = discord.Embed(color=discord.Color.gold(), description='')
        for page in self.paginator.pages:
            help_embed.description += page
        await destination.send(embed=help_embed)
