import os
import sqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv

import players

load_dotenv('./.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')

def main():
    con = sqlite3.connect('players.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM players")
    registered_players = players.list_from_tuples(cur.fetchall())

    bot = commands.Bot(command_prefix="t.", help_command=None, case_insensitive=True)

    @bot.command()
    async def register(ctx):
        if not user_registered(ctx.author):
            registered_players.append((ctx.author.id, ctx.author.name, 0))
            cur.execute("INSERT INTO players VALUES (?,?,?,?,?)", (ctx.author.id, ctx.author.name, 0))
            con.commit()
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")
 
    @bot.command(aliases=["p"])
    async def profile(ctx, *args):
        #TODO add mention profile
        if args and args[0]:
        if user_registered(ctx.author):
            player = get_player(ctx.author)
            profile = discord.Embed(title="{}'s Profile".format(player.name))
            profile.add_field(name="Money", value=player.money)
            await ctx.channel.send(embed=profile)
        else:
            await ctx.channel.send("{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))
 
    @bot.command()
    async def drive(ctx):
        drive_embed = discord.Embed(title="{} is driving".format(ctx.author.name),
                                    description="We hope he has fun")
        await ctx.channel.send(embed=drive_embed)

    @bot.command(aliases=["job"])
    async def quest(ctx):
        if user_registered(ctx.author):
            player = get_player(ctx.author)
            quest = discord.Embed(title="{}'s quest".format(player.name))
            await ctx.channel.send(embed=quest)
        else:
            await ctx.channel.send("{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))

    def user_registered(user):
        for player in registered_players:
            if user.id == player.user_id:
                return True
        return False
 
    def get_player(requested_player):
        for player in registered_players:
            if player.user_id == requested_player.id:
                return player
        return None

    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
