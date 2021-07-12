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
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def support(self, ctx) -> None:
        support_embed = discord.Embed(title="Click here to get to the support server",
                                      description="Any problems with the TruckSimulator? \n"
                                      "Report a bug or ask questions there :)",
                                      url="https://discord.gg/BKmtTFbvxv",
                                      colour=discord.Colour.gold())
        await ctx.channel.send(embed=support_embed)

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def github(self, ctx) -> None:
        support_embed = discord.Embed(title="Truck Simulator github repo",
                                      description="Check out the beautiful code behind the TruckSimulator or use the issue tracker to report bugs and problems",
                                      url="https://github.com/therealr5/TruckSimulatorBot",
                                      colour=discord.Colour.gold())
        await ctx.channel.send(embed=support_embed)

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def invite(self, ctx) -> None:
        support_embed = discord.Embed(title="Click here to add the bot to your servers",
                                      description="Go spread the word of the Truck Simulator",
                                      url="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&permissions=379904&scope=bot",
                                      colour=discord.Colour.gold())
        await ctx.channel.send(embed=support_embed)

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
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
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def links(self, ctx) -> None:
        links_embed = discord.Embed(title="Some useful links", colour=discord.Colour.gold())
        links_embed.add_field(name="Invite Link", value="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&permissions=379904&scope=bot", inline=False)
        links_embed.add_field(name="Github", value="https://www.github.com/therealr5/TruckSimulatorBot", inline=False)
        links_embed.add_field(name="Support server", value="https://discord.gg/BKmtTFbvxv", inline=False)
        links_embed.add_field(name="Top.gg page", value="Coming soon", inline=False)
        await ctx.channel.send(embed=links_embed)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def rechts(self, ctx) -> None:
        await ctx.channel.send("<:ts_actor:845028860361965598>")

