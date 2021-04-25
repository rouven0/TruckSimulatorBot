import os
import sqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv

import players
import symbols


load_dotenv('./.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')

def main():
    con = sqlite3.connect('players.db')
    cur = con.cursor()
    bot = commands.Bot(command_prefix="t.", help_command=None, case_insensitive=True)
    driving_players = []

    @bot.event
    async def on_ready():
        print("Connected to Discord")

    @bot.event
    async def on_reaction_add(reaction, user):
        """
        This method is only used to process the driving
        """
        if reaction.message.id not in get_drive_message_ids():
            return 
        driving_player = get_driving_player(user.id)
        if driving_player == None:
            return

        if reaction.emoji== "\N{OCTAGONAL SIGN}":
            driving_players.remove(get_driving_player(user.id))
            await reaction.message.clear_reactions() 
            await reaction.message.channel.send("You stopped driving!, {}".format(user.name))
            cur.execute("UPDATE players SET position=? WHERE id=?", (players.format_pos_to_db(driving_player.player.position), user.id))
            con.commit()

        position_changed = False
        if reaction.emoji == symbols.LEFT:
            driving_player.player.position = [driving_player.player.position[0]-1, driving_player.player.position[1]]
            position_changed = True

        if reaction.emoji == symbols.UP:
            driving_player.player.position = [driving_player.player.position[0], driving_player.player.position[1]+1]
            position_changed = True

        if reaction.emoji == symbols.DOWN:
            driving_player.player.position = [driving_player.player.position[0], driving_player.player.position[1]-1]
            position_changed = True

        if reaction.emoji == symbols.RIGHT:
            driving_player.player.position = [driving_player.player.position[0]+1, driving_player.player.position[1]]
            position_changed = True
        
        if position_changed:
            drive_embed = discord.Embed(title="{} is driving".format(user.name),
                                        description="We hope he has fun",
                                        colour=discord.Colour.gold())
            drive_embed.add_field(name="Instructions",
                                  value=open("./instrucions.md", "r").read(),
                                  inline=False)
            drive_embed.add_field(name="Note", value="You position is only applied if you stop driving", inline=False)
            drive_embed.add_field(name="Position", value=driving_player.player.position)
            await reaction.message.edit(embed=drive_embed)
            await reaction.message.clear_reactions() 
            for symbol in symbols.get_drive_position_symbols(driving_player.player.position):
                await reaction.message.add_reaction(symbol)
 
    @bot.command()
    async def register(ctx):
        if not user_registered(ctx.author.id):
            cur.execute("INSERT INTO players VALUES (?,?,?,?,?)", (ctx.author.id, ctx.author.name, 0, 0, "0/0"))
            con.commit()
            print("{} got registered".format(ctx.author.name))
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
    @commands.bot_has_permissions(manage_messages=True)
    async def drive(ctx):
        if user_registered(ctx.author.id):
            player = get_player(ctx.author.id)
            drive_embed = discord.Embed(title="{} is driving".format(ctx.author.name),
                                        description="We hope he has fun",
                                        colour=discord.Colour.gold())
            drive_embed.add_field(name="Instructions",
                                  value=open("./instrucions.md", "r").read(),
                                  inline=False)
            drive_embed.add_field(name="Note", value="You position is only applied if you stop driving", inline=False)
            drive_embed.add_field(name="Position", value=player.position)

            message = await ctx.channel.send(embed=drive_embed)
            for symbol in symbols.get_drive_position_symbols(player.position):
                await message.add_reaction(symbol)

            driving_players.append(players.DrivingPlayer(player, message))

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

    def get_driving_player(player_id):
        for driving_player in driving_players:
            if driving_player.player.user_id == player_id:
                return driving_player
        return None

    def get_drive_message_ids():
        ids = []
        for player in driving_players:
            ids.append(player.message.id)
        return ids 
    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
