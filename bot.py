import os
import sqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv

import players
import places
import symbols


load_dotenv('./.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')

def main():
    con = sqlite3.connect('players.db')
    cur = con.cursor()
    bot = commands.Bot(command_prefix="t.", help_command=None, case_insensitive=True)
    active_drives = []
    
    @bot.event
    async def on_ready():
        print("Connected to Discord")

    @bot.event
    async def on_reaction_add(reaction, user):
        """
        This method is only used to process the driving
        """
        if reaction.message.id not in [p.message.id for p in active_drives]:
            return 
        active_drive = get_active_drive(user.id)
        if active_drive == None:
            return

        if reaction.emoji== symbols.STOP:
            active_drives.remove(get_active_drive(user.id))
            await reaction.message.clear_reactions() 
            await reaction.message.channel.send("You stopped driving!, {}".format(user.name))
            cur.execute("UPDATE players SET position=? WHERE id=?", (players.format_pos_to_db(active_drive.player.position), user.id))
            con.commit()

        position_changed = False
        if reaction.emoji == symbols.LEFT:
            active_drive.player.position = [active_drive.player.position[0]-1, active_drive.player.position[1]]
            position_changed = True

        if reaction.emoji == symbols.UP:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1]+1]
            position_changed = True

        if reaction.emoji == symbols.DOWN:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1]-1]
            position_changed = True

        if reaction.emoji == symbols.RIGHT:
            active_drive.player.position = [active_drive.player.position[0]+1, active_drive.player.position[1]]
            position_changed = True
        
        if position_changed:
            await reaction.message.edit(embed=get_drive_embed(active_drive.player))
            await reaction.message.clear_reactions() 
            for symbol in symbols.get_drive_position_symbols(active_drive.player.position):
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
            profile = discord.Embed(title="{}'s Profile".format(player.name), colour=discord.Colour.gold())
            profile.add_field(name="Money", value=player.money)
            await ctx.channel.send(embed=profile)
        else:
            await ctx.channel.send("<@!{}> is not registered yet! Try `t.register` to get started".format(requested_id))
 
    @bot.command()
    @commands.bot_has_permissions(manage_messages=True)
    async def drive(ctx):
        if user_registered(ctx.author.id):
            player = get_player(ctx.author.id)
            message = await ctx.channel.send(embed=get_drive_embed(player))
            for symbol in symbols.get_drive_position_symbols(player.position):
                await message.add_reaction(symbol)
            active_drives.append(players.ActiveDrive(player, message))
        else:
            await ctx.channel.send("{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))

    def get_drive_embed(player): 
        place = places.get(player.position)
        drive_embed = discord.Embed(title="{} is driving".format(player.name),
                                    description="We hope he has fun",
                                    colour=discord.Colour.gold())
        drive_embed.add_field(name="Instructions",
                              value=open("./instrucions.md", "r").read(),
                              inline=False)
        drive_embed.add_field(name="Note", value="You position is only applied if you stop driving", inline=False)
        drive_embed.add_field(name="Position", value=player.position)
        if place is not None:
            drive_embed.set_image(url=place.image_url)
        else:
            drive_embed.set_image(url='https://cdn.discordapp.com/attachments/837784531267223552/837785502127489064/default.png')
        return drive_embed

    @bot.command(aliases=["here"])
    async def position(ctx):
        if user_registered(ctx.author.id):
            player = get_player(ctx.author.id)
            place = places.get(player.position)
            position_embed = discord.Embed(title="{}'s Position".format(ctx.author.name, colour=discord.Colour.gold()), 
                description="{}You are at {}".format(symbols.LIST_TITLE, player.position),
                colour=discord.Colour.gold())
            if place is not None:
                position_embed.add_field(name="What is here?", value=symbols.LIST_ITEM+place.name, inline=False)
                position_embed.add_field(name="Available Commands", value=get_place_commands(place.commands))
            else:
                position_embed.add_field(name="What is here?", value="Nothing :frowning:", inline=False)
            await ctx.channel.send(embed=position_embed)
        else:
            await ctx.channel.send("{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))
 
    def get_place_commands(command_list):
        readable = ""
        for command in command_list:
            readable = "{}{}`{}`\n".format(readable, symbols.LIST_ITEM, command)
        return readable

    @bot.command(aliases=["places"])
    async def addressbook(ctx):
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.gold())   
        for place in places.get_all():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.channel.send(embed=places_embed)

    @bot.command()
    async def bing(ctx):
        await ctx.channel.send("Bong")

    def user_registered(user_id):
        cur.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
        if len(cur.fetchall()) == 1:
            return True
        else:
            return False
 
    def get_player(user_id):
        cur.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
        return players.from_tuple(cur.fetchone())

    def get_active_drive(player_id):
        for active_drive in active_drives:
            if active_drive.player.user_id == player_id:
                return active_drive
        return None

    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
