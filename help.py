import discord
from discord.errors import Forbidden
from discord.ext import commands


class TruckSimulatorHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        help_embed = discord.Embed(color=discord.Color.gold(), description='')
        for page in self.paginator.pages:
            help_embed.description += page
        try:
            await destination.send(embed=help_embed)
        except Forbidden as e:
            await destination.send("Hey there, please make shure that the bot has the following permissions: \n"
                    "``` view_channel \n send_messages \n embed_links \n attach_files \n use_external_emojis \n read_message_history```")
