"""
This module contains the Cog for all stat-related commands
"""
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
import jobs
import players
import trucks
import levels


class Stats(commands.Cog):
    """
    A lot of numbers
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @cog_ext.cog_subcommand(base="profile", guild_ids=[830928381100556338])
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def register(self, ctx) -> None:
        """
        Register yourself in a stunningly beautiful database
        """
        welcome_file = open("./messages/welcome.md", "r")
        welcome_embed = discord.Embed(title="Hey there, fellow Trucker,", description=welcome_file.read(),
                                      colour=discord.Colour.gold())
        welcome_file.close()
        welcome_embed.set_author(name="Welcome to the Truck Simulator", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=welcome_embed)
        if not await players.registered(ctx.author.id):
            await players.insert(players.Player(ctx.author.id, ctx.author.name, money=1000))
            await ctx.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.send("You are already registered")

    @cog_ext.cog_subcommand(base="profile", guild_ids=[830928381100556338])
    async def delete(self, ctx) -> None:
        """
        Delete your account
        """
        player = await players.get(ctx.author.id)
        await ctx.send("{} Are you sure you want to delete your profile? "
                               "**All your ingame stats will be lost!**".format(ctx.author.mention))
        confirmation = "delete {}@trucksimulator".format(ctx.author.name)
        await ctx.send("Please type **`{}`** to confirm your deletion".format(confirmation))

        def check(message):
            return message.author.id == ctx.author.id

        try:
            answer_message: discord.Message = await self.bot.wait_for('message', check=check, timeout=120)
            answer = answer_message.content.lower()
        except:
            answer = ""
        if answer == confirmation:
            await players.remove(player)
            job = jobs.get(ctx.author.id)
            if job is not None:
                jobs.remove(job)
            await ctx.send("Your profile got deleted. We will miss you :(")
        else:
            await ctx.send("Deletion aborted!")

    @cog_ext.cog_subcommand(base="profile", name="show", guild_ids=[830928381100556338])
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def profile(self, ctx, user: discord.User = None) -> None:
        """
        Shows your in-game profile. That's it
        """
        profile_embed = discord.Embed(colour=discord.Colour.gold())
        if user is not None:
            player = await players.get(user.id)
            profile_embed.set_thumbnail(url=user.avatar_url)
            profile_embed.set_author(name="{}'s Profile".format(player.name),
                                     icon_url=user.avatar_url)
        else:
            player = await players.get(ctx.author.id)
            profile_embed.set_thumbnail(url=ctx.author.avatar_url)
            profile_embed.set_author(name="{}'s Profile".format(player.name),
                                     icon_url=ctx.author.avatar_url)
            # Detect, when the player is renamed
            if player.name != ctx.author.name:
                await players.update(player, name=ctx.author.name)

        truck = trucks.get(player.truck_id)
        xp = "{:,}".format(player.xp)
        next_xp = "{:,}".format(levels.get_next_xp(player.level))
        money = "{:,}".format(player.money)
        miles = "{:,}".format(player.miles)
        truck_miles = "{:,}".format(player.truck_miles)
        profile_embed.add_field(name="Level", value=f"{player.level} ({xp}/{next_xp} xp)", inline=False)
        profile_embed.add_field(name="Money", value=f"${money}")
        profile_embed.add_field(name="Miles driven", value=f"{miles}\n({truck_miles} with current truck)",
                                inline=False)
        profile_embed.add_field(name="Gas left", value=f"{player.gas} l", inline=False)
        profile_embed.add_field(name="Current truck", value=truck.name)
        profile_embed.set_image(url=truck.image_url)
        await ctx.send(embed=profile_embed)

    @cog_ext.cog_slash(guild_ids=[830928381100556338],
            options=[
                create_option(
                    name="key",
                    description="The list you want to view",
                    option_type=3,
                    choices=["level", "money", "miles"],
                    required=True)])

    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def top(self, ctx, key) -> None:
        """
        If you appear in these lists you are one of the top 10 Players. Congratulations!
        """
        top_players = await players.get_top(key)
        top_body = ""
        count = 0
        top_embed = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())

        for player in top_players[0]:
            if key == "money":
                val = "{:,}".format(player.money)
            elif key == "miles":
                val = "{:,}".format(player.miles)
            else:
                val = "{:,} ({}/{} xp)".format(player.level, player.xp, levels.get_next_xp(player.level))
                top_embed.set_footer(text="You can also sort by money and miles", icon_url=self.bot.user.avatar_url)
            count += 1
            top_body += "**{}**. {} ~ {}{}\n".format(count, player.name,
                                                      val, top_players[1])
        top_embed.add_field(name=f"Top {key}", value=top_body)
        await ctx.send(embed=top_embed)
