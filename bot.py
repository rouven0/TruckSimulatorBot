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
    bot = commands.Bot(command_prefix="t.", help_command=None, case_insensitive=True)

    @bot.event
    async def on_ready():
        print("Connected to Discord")

    @bot.command()
    async def register(ctx):
        if not user_registered(ctx.author.id):
            cur.execute("INSERT INTO players VALUES (?,?,?,?,?)", (ctx.author.id, ctx.author.name, 0, 0, 0))
            con.commit()
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")

    @bot.command(aliases=["p", "me"])
    async def profile(ctx, *args):
        requested_id = ""
        if args and args[0].startswith("<@!"):
            requested_id = int(args[0][args[0].find("!")+1:args[0].find(">")])
        else:
            requested_id = ctx.author.id

        if user_registered(requested_id):
            player = get_player(requested_id)
            profile = discord.Embed(title="{}'s Profile".format(player.name))
            profile.add_field(name="Money", value=player.money)
            await ctx.channel.send(embed=profile)
        else:
            await ctx.channel.send("<@!{}> is not registered yet! Try `t.register` to get started".format(requested_id))
 
    @bot.command()
    async def drive(ctx):
        if user_registered(ctx.author.id):
            drive_embed = discord.Embed(title="{} is driving".format(ctx.author.name),
                                        description="We hope he has fun")
            await ctx.channel.send(embed=drive_embed)
        else:
            await ctx.channel.send("{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))

    @bot.command(aliases=["job"])
    async def quest(ctx):
        # TODO make 
        if user_registered(ctx.author.id):
            player = get_player(ctx.author.id)
            quest = discord.Embed(title="{}'s quest".format(player.name))
            await ctx.channel.send(embed=quest)
        else:
            await ctx.channel.send("{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))

    def user_registered(user_id):
        cur.execute("SELECT * FROM players")
        for player in cur.fetchall():
            if user_id == player[0]:
                return True
        return False
 
    def get_player(player_id):
        cur.execute("SELECT * FROM players")
        for player in players.list_from_tuples(cur.fetchall()):
            if player.user_id == player_id:
                return player
        return None

    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
