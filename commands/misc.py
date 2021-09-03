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

    @cog_ext.cog_subcommand(base="links")
    async def support(self, ctx) -> None:
        """
        Truck Simulator support server
        """
        support_embed = discord.Embed(
            title="Click here to get to the support server",
            description="Any problems with the TruckSimulator? \n" "Report a bug or ask questions there :)",
            url="https://discord.gg/BKmtTFbvxv",
            colour=discord.Colour.gold(),
        )
        await ctx.send(embed=support_embed)

    @cog_ext.cog_subcommand(base="links")
    async def github(self, ctx) -> None:
        """
        The truck simulator github repo
        """
        support_embed = discord.Embed(
            title="Truck Simulator github repo",
            description="Check out the beautiful code behind the TruckSimulator or use the issue tracker to report bugs and problems",
            url="https://github.com/therealr5/TruckSimulatorBot",
            colour=discord.Colour.gold(),
        )
        await ctx.send(embed=support_embed)

    @cog_ext.cog_subcommand(base="links")
    async def invite(self, ctx) -> None:
        """
        Invite the truck simulator to your servers
        """
        support_embed = discord.Embed(
            title="Click here to add the bot to your servers",
            description="Go spread the word of the Truck Simulator",
            url="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&permissions=3072&scope=bot%20applications.commands",
            colour=discord.Colour.gold(),
        )
        await ctx.send(embed=support_embed)

    @cog_ext.cog_slash()
    async def rules(self, ctx) -> None:
        """
        Truck Simulator rules
        """
        rules_embed = discord.Embed(title="Truck Simulator Ingame Rules", colour=discord.Colour.gold())
        rules_embed.add_field(
            name="Trading ingame currency for real money",
            value="Not only that is is pretty stupid to trade real world's money in exchange of a number "
            "somewhere in a random database it will also get you banned from this bot.",
            inline=False,
        )
        rules_embed.add_field(
            name="Autotypers",
            value="Since it's quite hard to write them for the Truck Simulator and it's a good amount "
            "of work, people who manage to write (working) automation software for this bot will "
            "not get banned. But people who use them will be.",
        )
        await ctx.send(embed=rules_embed)

    @cog_ext.cog_slash(guild_ids=[839580174282260510, 830928381100556338])
    async def serverrules(self, ctx) -> None:
        """
        Truck Simulator server rules
        """
        rules_embed = discord.Embed(title="Truck Simulator Server Rules", colour=discord.Colour.gold())
        rules_embed.add_field(
            name="Be civil and respectful",
            value="Treat everyone with respect. Absolutely no harassment, witch hunting, sexism, racism, "
            "or hate speech will be tolerated.",
            inline=False,
        )
        rules_embed.add_field(
            name="No spam or self-promotion",
            value="No spam or self-promotion (server invites, advertisements, etc) without permission "
            "from a staff member. This includes DMing fellow members.",
            inline=False,
        )
        rules_embed.add_field(
            name="No NSFW or obscene content",
            value="This includes text, images, or links featuring nudity, sex, hard violence, "
            "or other graphically disturbing content.",
            inline=False,
        )
        await ctx.send(embed=rules_embed)

    @cog_ext.cog_subcommand(base="links")
    async def all(self, ctx) -> None:
        """
        All the links in a beautiful list
        """
        links_embed = discord.Embed(title="Some useful links", colour=discord.Colour.gold())
        links_embed.add_field(
            name="Invite Link",
            value="https://discord.com/api/oauth2/authorize?client_id=831052837353816066&permissions=3072&scope=bot%20applications.commands",
            inline=False,
        )
        links_embed.add_field(name="Github", value="https://www.github.com/therealr5/TruckSimulatorBot", inline=False)
        links_embed.add_field(name="Support server", value="https://discord.gg/BKmtTFbvxv", inline=False)
        links_embed.add_field(name="Top.gg page", value="https://top.gg/bot/831052837353816066", inline=False)
        await ctx.send(embed=links_embed)

    @cog_ext.cog_slash()
    @commands.bot_has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        use_external_emojis=True,
    )
    async def vote(self, ctx) -> None:
        """
        Support the bot by voting for it on top.gg
        """
        vote_embed = discord.Embed(
            title="Click here to vote for the Truck Simulator",
            description="There are no rewards yet :frowning: , do it if you want to support this bot.",
            url="https://top.gg/bot/831052837353816066/vote",
            colour=discord.Colour.gold(),
        )
        await ctx.send(embed=vote_embed)

    @cog_ext.cog_slash()
    async def credits(self, ctx) -> None:
        """
        Wonderful people
        """
        await ctx.send(
            embed=discord.Embed(
                title="All the wonderful persons that helped the Truck Simulator evolve",
                description="**LeBogo** - _Testing helper_ - Contributed 2 lines of code\n"
                "**FlyingPanda** - _EPIC Artist_ - Drew almost all of the images you see (and had the idea of this bot)\n"
                "**Miriel** - _The brain_ - Gave a lot of great tips and constructive feedback",
                colour=discord.Colour.gold(),
            )
        )
