"""
This module contains a Cog for all the commands, that don't have a speciefied category
"""
import discord
from discord.ext import commands
from discord_slash import cog_ext


class Misc(commands.Cog):
    """
    All commands I can't find a category to
    """

    @cog_ext.cog_slash()
    async def support(self, ctx) -> None:
        """
        Truck Simulator support server
        """
        support_embed = discord.Embed(
            title="Click here to get to the support server",
            description="Any problems with the TruckSimulator? \n" "Report a bug or ask questions there :)",
            url="https://discord.gg/FzAxtGTUhN",
            colour=discord.Colour.lighter_grey(),
        )
        await ctx.send(embed=support_embed)

    @cog_ext.cog_slash()
    async def invite(self, ctx) -> None:
        """
        Invite the truck simulator to your servers
        """
        support_embed = discord.Embed(
            title="Click here to add the bot to your servers",
            description="Go spread the word of the Truck Simulator",
            url="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&scope=applications.commands",
            colour=discord.Colour.lighter_grey(),
        )
        await ctx.send(embed=support_embed)

    @cog_ext.cog_slash()
    async def rules(self, ctx) -> None:
        """
        Truck Simulator rules
        """
        rules_embed = discord.Embed(title="Truck Simulator Ingame Rules", colour=discord.Colour.lighter_grey())
        rules_embed.add_field(
            name="Trading ingame currency for real money",
            value="Not only that it is pretty stupid to trade real world's money in exchange of a number "
            "somewhere in a random database it will also get you banned from this bot.",
            inline=False,
        )
        rules_embed.add_field(
            name="Autotypers",
            value="Don't even try, it's just wasted work only to get you blacklisted.",
        )
        await ctx.send(embed=rules_embed)

    @cog_ext.cog_slash()
    async def vote(self, ctx) -> None:
        """
        Support the bot by voting for it on top.gg
        """
        vote_embed = discord.Embed(
            title="Click here to vote for the Truck Simulator",
            description="If you are a member of the official server, you will get a special color role for 12 hours",
            url="https://top.gg/bot/831052837353816066/vote",
            colour=discord.Colour.lighter_grey(),
        )
        await ctx.send(embed=vote_embed)

    @cog_ext.cog_slash()
    async def complain(self, ctx) -> None:
        await ctx.send(
            "What a crap bot this is! :rage: "
            "Hours of time wasted on this useless procuct of a terrible coder and a lousy artist "
            ":rage: :rage: Is this bot even TESTED before the updates are published... "
            "Horrible, just HORRIBLE this spawn of incopetence. Who tf made this? A 12 year old child? "
            "This child would probably have made it better than THAT :rage: "
            'The core system is buggy the economy is unbalanced and there is no goal in this _"game bot"_ :rage:'
        )
