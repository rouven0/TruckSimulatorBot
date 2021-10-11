"""
This module contains the Cog for all stat-related commands
"""
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import MenuContext
from discord_slash.utils.manage_commands import create_option
import api.players as players
import api.trucks as trucks
import api.levels as levels


class Stats(commands.Cog):
    """
    A lot of numbers
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @cog_ext.cog_subcommand(base="profile")
    async def register(self, ctx) -> None:
        """
        Register yourself in a stunningly beautiful database
        """
        welcome_file = open("./messages/welcome.md", "r")
        welcome_embed = discord.Embed(
            title="Hey there, fellow Trucker,", description=welcome_file.read(), colour=discord.Colour.lighter_grey()
        )
        welcome_file.close()
        welcome_embed.set_author(name="Welcome to the Truck Simulator", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=welcome_embed)
        if not await players.registered(ctx.author.id):
            await players.insert(players.Player(ctx.author.id, ctx.author.name, money=1000))
            await ctx.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.send("You are already registered")

    @cog_ext.cog_subcommand(base="profile", name="show")
    async def profile(self, ctx, user: discord.User = None) -> None:
        """
        Shows your in-game profile. That's it
        """
        if isinstance(user, str):
            user = await self.bot.fetch_user(int(user))
        if user is not None:
            target_user = user
        else:
            target_user = ctx.author
        await ctx.send(embed=await self.get_profile_embed(target_user.id))

    @cog_ext.cog_context_menu(name="Check Profile", target=2)
    async def context_profile(self, ctx: MenuContext) -> None:
        await ctx.send(embed=await self.get_profile_embed(ctx.target_id), hidden=True)

    async def get_profile_embed(self, user_id: int) -> discord.Embed:
        profile_embed = discord.Embed(colour=discord.Colour.lighter_grey())
        user = self.bot.get_user(user_id)
        if user is None:
            user = await self.bot.fetch_user(user_id)
        player = await players.get(user.id)
        profile_embed.set_thumbnail(url=user.avatar_url)
        profile_embed.set_author(name="{}'s Profile".format(player.name), icon_url=user.avatar_url)
        truck = trucks.get(player.truck_id)
        xp = "{:,}".format(player.xp)
        next_xp = "{:,}".format(levels.get_next_xp(player.level))
        money = "{:,}".format(player.money)
        miles = "{:,}".format(player.miles)
        truck_miles = "{:,}".format(player.truck_miles)
        profile_embed.add_field(name="Level", value=f"{player.level} ({xp}/{next_xp} xp)", inline=False)
        profile_embed.add_field(name="Money", value=f"${money}")
        profile_embed.add_field(name="Miles driven", value=f"{miles}\n({truck_miles} with current truck)", inline=False)
        profile_embed.add_field(name="Gas left", value=f"{player.gas} l", inline=False)
        profile_embed.add_field(name="Current truck", value=truck.name)
        profile_embed.set_image(url=truck.image_url)
        return profile_embed

    @cog_ext.cog_slash(
        options=[
            create_option(
                name="key",
                description="The list you want to view",
                option_type=3,
                choices=["level", "money", "miles"],
                required=True,
            )
        ]
    )
    async def top(self, ctx, key) -> None:
        """
        If you appear in these lists you are one of the top 10 Players. Congratulations!
        """
        top_players = await players.get_top(key)
        top_body = ""
        count = 0
        top_embed = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.lighter_grey())

        for player in top_players[0]:
            if key == "money":
                val = "{:,}".format(player.money)
            elif key == "miles":
                val = "{:,}".format(player.miles)
            else:
                val = "{:,} ({}/{} xp)".format(player.level, player.xp, levels.get_next_xp(player.level))
                top_embed.set_footer(text="You can also sort by money and miles", icon_url=self.bot.user.avatar_url)
            count += 1
            top_body += "**{}**. {} ~ {}{}\n".format(count, player.name, val, top_players[1])
        top_embed.add_field(name=f"Top {key}", value=top_body)
        await ctx.send(embed=top_embed)
