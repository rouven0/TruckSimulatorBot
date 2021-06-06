import discord
from discord.ext import commands
import jobs
import players


class Stats(commands.Cog):
    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def register(self, ctx):
        if not players.registered(ctx.author.id):
            players.insert(players.Player(ctx.author.id, ctx.author.name))
            print("{} got registered".format(ctx.author.name))
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")

    @commands.command(aliases=["p", "me"])
    async def profile(self, ctx, *args):
        if args and args[0].startswith("<@"):
            if args[0].find("!") != -1:
                requested_id = int(args[0][args[0].find("!") + 1:args[0].find(">")])
            else:
                requested_id = int(args[0][args[0].find("@") + 1:args[0].find(">")])
        else:
            requested_id = ctx.author.id

        player = players.get(requested_id)
        if player is None:
            await ctx.channel.send("<@!{}> is not registered yet! "
                                   "Try `t.register` to get started".format(requested_id))
            return

        current_job = jobs.get(ctx.author.id)
        profile_embed = discord.Embed(colour=discord.Colour.gold())
        profile_embed.set_author(name="{}'s Profile".format(player.name), icon_url=ctx.author.avatar_url)
        profile_embed.set_thumbnail(url=ctx.author.avatar_url)
        profile_embed.add_field(name="Money", value=player.money)
        profile_embed.add_field(name="Miles driven", value=player.miles, inline=False)
        if current_job is not None:
            profile_embed.add_field(name="Current Job", value=jobs.show(current_job))
        await ctx.channel.send(embed=profile_embed)

    @commands.command()
    async def top(self, ctx, *args):
        if args:
            top_players = players.get_top(args[0])
        else:
            top_players = players.get_top()
        top_body = ""
        count = 0

        for player in top_players[0]:
            if top_players[1] == "money":
                val = player.money
            else:
                val = player.miles
            count += 1
            top_body = "{}**{}**. {} - {}{}\n".format(top_body, count, player.name, val, top_players[2])
        top_emded = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())
        top_emded.add_field(name="Top {}".format(top_players[1]), value=top_body)
        await ctx.channel.send(embed=top_emded)
