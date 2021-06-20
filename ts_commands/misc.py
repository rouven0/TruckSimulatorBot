"""
This module contains a Cog for all the commands, that don't have a speciefied category
"""
import discord
from discord.ext import commands


class Misc(commands.Cog):
    """
    All commands I can't find a category to
    """
    @commands.command()
    async def links(self, ctx):
        """
        Some useful links
        """
        links_embed = discord.Embed(title="Some useful links", colour=discord.Colour.gold())
        links_embed.add_field(name="Github", value="https://www.github.com/therealr5/TruckSimulatorBot", inline=False)
        links_embed.add_field(name="Support server", value="https://discord.gg/CjBpA6ReFz", inline=False)
        links_embed.add_field(name="Top.gg page", value="Coming soon", inline=False)
        await ctx.channel.send(embed=links_embed)

    @commands.command(hidden=True)
    async def rechts(self, ctx):
        await ctx.channel.send("<:ts_actor:845028860361965598>")

