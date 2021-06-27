"""
This module contains the Cog for all stat-related commands
"""
import discord
from discord.ext import commands
import jobs
import players


class Stats(commands.Cog):
    """
    A lot of numbers
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def register(self, ctx) -> None:
        """
        Register yourself in a stunningly beautiful database that will definitely not deleted by accident anymore
        """
        if not players.registered(ctx.author.id):
            players.insert(players.Player(ctx.author.id, ctx.author.name))
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")

    @commands.command()
    async def delete(self, ctx) -> None:
        """
        Delete your account
        """
        player = players.get(ctx.author.id)
        await ctx.channel.send("{} Are you sure you want to delete your profile? "
                               "**All your ingame stats will be lost!**".format(ctx.author.mention))
        confirmation = "delete {}@trucksimulator".format(ctx.author.name)
        await ctx.channel.send("Please type **`{}`** to confirm your deletion".format(confirmation))
        def check(message):
            return message.author.id == ctx.author.id
        try:
            answer_message: discord.Message = await self.bot.wait_for('message', check=check,  timeout=120)
            answer = answer_message.content.lower()
        except:
            answer = ""
        if answer == confirmation:
            players.remove(player)
            job = jobs.get(ctx.author.id)
            if job is not None:
                jobs.remove(job)
            await ctx.channel.send("Your profile got deleted. We will miss you :(")
        else:
            await ctx.channel.send("Deletion aborted!")

    @commands.command(aliases=["p", "me"])
    async def profile(self, ctx, user: discord.Member=None) -> None:
        """
        Shows your in-game profile. That's it
        """
        profile_embed = discord.Embed(colour=discord.Colour.gold())
        if user is not None:
            player = players.get(user.id)
            profile_embed.set_thumbnail(url=user.avatar_url)
            profile_embed.set_author(name="{}'s Profile".format(player.name),
                                     icon_url=user.avatar_url)
        else:
            player = players.get(ctx.author.id)
            profile_embed.set_thumbnail(url=ctx.author.avatar_url)
            profile_embed.set_author(name="{}'s Profile".format(player.name),
                                     icon_url=ctx.author.avatar_url)
            # Detect, when the player is renamed
            if player.name != ctx.author.name:
                players.update(player, name=ctx.author.name)

        profile_embed.add_field(name="Money", value=player.money)
        profile_embed.add_field(name="Miles driven", value=player.miles, inline=False)
        current_job = jobs.get(ctx.author.id)
        if current_job is not None:
            profile_embed.add_field(name="Current Job", value=jobs.show(current_job))
        await ctx.channel.send(embed=profile_embed)

    @commands.command()
    async def top(self, ctx, key="level") -> None:
        """
        If you appear in these lists you are one of the top 10 Players. Congratulations!
        """
        top_players = players.get_top(key)
        top_body = ""
        top_title = "level"
        count = 0

        for player in top_players[0]:
            if top_players[1] == "money":
                val = player.money
                top_title = top_players[1]
            elif top_players[1] == "miles":
                val = player.miles
                top_title = top_players[1]
            else:
                val = player.level
            count += 1
            top_body = "{}**{}**. {} - {}{}\n".format(top_body, count, player.name,
                                                      val, top_players[2])
        top_embed = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())
        top_embed.add_field(name="Top {}".format(top_title), value=top_body)
        await ctx.channel.send(embed=top_embed)
