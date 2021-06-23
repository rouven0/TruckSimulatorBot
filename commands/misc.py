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
    async def support(self, ctx) -> None:
        support_embed = discord.Embed(title="Click here to get to the support server",
                                      description="Any problems with the TruckSimulator? \n"
                                      "Report a bug or ask questions there :)",
                                      url="https://discord.gg/BKmtTFbvxv",
                                      colour=discord.Colour.gold())
        await ctx.channel.send(embed=support_embed)

    @commands.command()
    async def rules(self, ctx) -> None:
        rules_embed=discord.Embed(title="Truck Simulator Rules",
                                  colour=discord.Colour.gold())
        rules_embed.add_field(name="Trading ingame currency for real money",
                              value="Not only that is is pretty stupid to trade real world's money in exchange of a number "
                                    "somewhere in a random database it will also get you banned from this bot.",
                                    inline=False)
        rules_embed.add_field(name="Autotypers",
                              value="Since it's quite hard to write them for the Truck Simulator and it's a good amount "
                                    "of work, people who manage to write (working) automation software for this bot will "
                                    "not get banned. But people who use them will be.")
        await ctx.channel.send(embed=rules_embed)

    @commands.command()
    async def links(self, ctx) -> None:
        """
        Some useful links
        """
        links_embed = discord.Embed(title="Some useful links", colour=discord.Colour.gold())
        links_embed.add_field(name="Github", value="https://www.github.com/therealr5/TruckSimulatorBot", inline=False)
        links_embed.add_field(name="Support server", value="https://discord.gg/BKmtTFbvxv", inline=False)
        links_embed.add_field(name="Top.gg page", value="Coming soon", inline=False)
        await ctx.channel.send(embed=links_embed)

    @commands.command(hidden=True)
    async def rechts(self, ctx) -> None:
        await ctx.channel.send("<:ts_actor:845028860361965598>")

