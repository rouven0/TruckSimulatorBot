"""
This module contains the Cog for all stat-related commands
"""
import discord
from discord.ext import commands
import jobs
import players
import levels


class Stats(commands.Cog):
    """
    A lot of numbers
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def register(self, ctx) -> None:
        """
        Register yourself in a stunningly beautiful database that will definitely not deleted by accident anymore
        """
        welcome_file = open("./messages/welcome.md", "r")
        welcome_embed = discord.Embed(title="Hey there, fellow Trucker,", description=welcome_file.read(),
                                      colour=discord.Colour.gold())
        welcome_file.close()
        welcome_embed.set_author(name="Welcome to the Truck Simulator", icon_url=self.bot.user.avatar_url)
        await ctx.channel.send(embed=welcome_embed)
        if not await players.registered(ctx.author.id):
            await players.insert(players.Player(ctx.author.id, ctx.author.name, money=1000))
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")

    @commands.command()
    async def delete(self, ctx) -> None:
        """
        Delete your account
        """
        player = await players.get(ctx.author.id)
        await ctx.channel.send("{} Are you sure you want to delete your profile? "
                               "**All your ingame stats will be lost!**".format(ctx.author.mention))
        confirmation = "delete {}@trucksimulator".format(ctx.author.name)
        await ctx.channel.send("Please type **`{}`** to confirm your deletion".format(confirmation))

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
            await ctx.channel.send("Your profile got deleted. We will miss you :(")
        else:
            await ctx.channel.send("Deletion aborted!")

    @commands.command(aliases=["p", "me"])
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
        await ctx.channel.send(embed=profile_embed)

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def top(self, ctx, key="level") -> None:
        """
        If you appear in these lists you are one of the top 10 Players. Congratulations!
        """
        top_players = await players.get_top(key.lower())
        top_body = ""
        top_title = "level"
        count = 0
        top_embed = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())

        for player in top_players[0]:
            if top_players[1] == "money":
                val = "{:,}".format(player.money)
                top_title = top_players[1]
            elif top_players[1] == "miles":
                val = "{:,}".format(player.miles)
                top_title = top_players[1]
            else:
                val = "{:,} ({}/{} xp)".format(player.level, player.xp, levels.get_next_xp(player.level))
                top_embed.set_footer(text="You can also sort by money and miles", icon_url=self.bot.user.avatar_url)
            count += 1
            top_body += "**{}**. {} ~ {}{}\n".format(count, player.name,
                                                      val, top_players[2])
        top_embed.add_field(name="Top {}".format(top_title), value=top_body)
        await ctx.channel.send(embed=top_embed)
