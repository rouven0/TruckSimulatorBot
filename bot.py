import os
import sqlite3
from time import time
from datetime import datetime
from math import floor
from importlib import reload
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

import assets
import config
# import help
import players
import places
import symbols

load_dotenv('./.env')
# BOT_TOKEN = os.getenv('BOT_TOKEN')

# Alternate token for testing. Uncomment if needed
# remove this if the bot is transferred to a remote server, only the real token will be stored then
BOT_TOKEN = os.getenv('TEST_BOT_TOKEN')

def main():
    con = sqlite3.connect('players.db')
    cur = con.cursor()
    bot = commands.Bot(command_prefix=["t.", "T."],
                       help_command=discord.ext.commands.DefaultHelpCommand(),
                       case_insensitive=True)
    active_drives = []

    @bot.event
    async def on_ready():
        print("Connected to Discord")
        await bot.change_presence(status=discord.Status.online,
                                  activity=discord.Activity(
                                      type=discord.ActivityType.watching,
                                      name="the hills passing by"))

    @bot.event
    async def on_reaction_add(reaction, user):
        """
        This method is only used to process the driving
        """
        if reaction.message.id not in [p.message.id for p in active_drives]:
            return
        active_drive = get_active_drive(user.id, reaction.message.id)
        if active_drive is None:
            return
        if active_drive.islocked:
            return

        if reaction.emoji == symbols.STOP:
            active_drives.remove(get_active_drive(user.id, reaction.message.id))
            await reaction.message.clear_reactions()
            await reaction.message.channel.send("You stopped driving!, {}".format(user.name))
            cur.execute("UPDATE players SET position=? WHERE id=?",
                        (players.format_pos_to_db(active_drive.player.position), user.id))
            cur.execute("UPDATE players SET miles=? WHERE id=?",
                        (active_drive.player.miles, user.id))
            con.commit()

        position_changed = False
        if reaction.emoji == symbols.LEFT:
            active_drive.player.position = [active_drive.player.position[0] - 1,
                                            active_drive.player.position[1]]
            position_changed = True

        if reaction.emoji == symbols.UP:
            active_drive.player.position = [active_drive.player.position[0],
                                            active_drive.player.position[1] + 1]
            position_changed = True

        if reaction.emoji == symbols.DOWN:
            active_drive.player.position = [active_drive.player.position[0],
                                            active_drive.player.position[1] - 1]
            position_changed = True

        if reaction.emoji == symbols.RIGHT:
            active_drive.player.position = [active_drive.player.position[0] + 1,
                                            active_drive.player.position[1]]
            position_changed = True

        if position_changed:
            active_drive.islocked = True
            active_drive.last_action_time = time()
            active_drive.player.miles += 1
            await reaction.message.edit(embed=get_drive_embed(active_drive.player))
            if (active_drive.player.position[0] >= config.MAP_BORDER or
                    active_drive.player.position[1] >= config.MAP_BORDER or
                    active_drive.player.position[0] < 1 or
                    active_drive.player.position[1] < 1):
                await reaction.message.clear_reactions()
                # clear the local list to get the missing symbols done properly
                reaction.message.reactions = []
            else:
                await reaction.remove(user)

            missing_symbols = False
            for symbol in symbols.get_drive_position_symbols(active_drive.player.position):
                if symbol not in [r.emoji for r in reaction.message.reactions]:
                    missing_symbols = True
            if missing_symbols:
                await reaction.message.clear_reactions()
                for symbol in symbols.get_drive_position_symbols(active_drive.player.position):
                    await reaction.message.add_reaction(symbol)
            active_drive.islocked = False
 
    async def check_drives():
        while True:
            for drive in active_drives:
                if time() -  drive.last_action_time > 300:
                    active_drives.remove(drive)
                    await drive.message.clear_reactions()
                    await drive.message.channel.send("<@{}> You left your truck but forgot to stop driving. Luckily a friendly Gnome stopped you at the end of the map".format(drive.player.user_id))
                    cur.execute("UPDATE players SET position=? WHERE id=?",
                                ("50/50", drive.player.user_id))
                    cur.execute("UPDATE players SET miles=? WHERE id=?",
                                (drive.player.miles, drive.player.user_id))
                    con.commit()
            await asyncio.sleep(10)

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def register(ctx):
        # id, name, truck_id, money, posittion, quest_items, quest_from, quest_to, miles
        if not user_registered(ctx.author.id):
            cur.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?)",
                        (ctx.author.id, ctx.author.name, 0, 0, "0/0", "", "0/0", "0/0", 0))
            con.commit()
            print("{} got registered".format(ctx.author.name))
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")

    @bot.command(aliases=["p", "me"])
    async def profile(ctx, *args):
        if args and args[0].startswith("<@"):
            if args[0].find("!") != -1:
                requested_id = int(args[0][args[0].find("!") + 1:args[0].find(">")])
            else:
                requested_id = int(args[0][args[0].find("@") + 1:args[0].find(">")])
        else:
            requested_id = ctx.author.id

        if user_registered(requested_id):
            player = get_player(requested_id)
            profile_embed = discord.Embed(title="{}'s Profile".format(player.name),
                                          colour=discord.Colour.gold())
            profile_embed.add_field(name="Money", value=player.money, inline=False)
            profile_embed.add_field(name="Miles driven", value=player.miles)
            await ctx.channel.send(embed=profile_embed)
        else:
            await ctx.channel.send("<@!{}> is not registered yet! Try `t.register` to get started".format(requested_id))

    @bot.command()
    async def top(ctx, *args):
        if args and args[0] == "money":
            request = "money"
            cur.execute('SELECT * FROM players ORDER BY money DESC')
        else:
            request = "miles"
            cur.execute('SELECT * FROM players ORDER BY miles DESC')
        top_embed = players.list_from_tuples(cur.fetchmany(10))
        top_body = ""
        count = 0
        for player in top_embed:
            if request == "miles":
                val = player.miles
            if request == "money":
                val = player.money

            count += 1
            top_body = "{}**{}**. {} - {} {}\n".format(top_body, count, player.name, val, request)
        top_emded = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())
        top_emded.add_field(name="Top {}".format(request), value=top_body)
        await ctx.channel.send(embed=top_emded)

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def drive(ctx):
        if not user_registered(ctx.author.id):
            await ctx.channel.send(
                "{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))
            return

        if ctx.author.id in [a.player.user_id for a in active_drives]:
            await ctx.channel.send("You can't drive on two roads at once!")
            return

        player = get_player(ctx.author.id)
        message = await ctx.channel.send(embed=get_drive_embed(player))
        for symbol in symbols.get_drive_position_symbols(player.position):
            await message.add_reaction(symbol)
        active_drives.append(players.ActiveDrive(player, message, time()))

    def get_drive_embed(player):
        place = places.get(player.position)
        drive_embed = discord.Embed(title="{} is driving".format(player.name),
                                    description="We hope he has fun",
                                    colour=discord.Colour.gold())
        drive_embed.add_field(name="Instructions",
                              value=open("./drive_instrucions.md", "r").read(),
                              inline=False)
        drive_embed.add_field(name="Note",
                              value="Your position is only applied if you stop driving",
                              inline=False)
        drive_embed.add_field(name="Position", value=player.position)
        if place is not None:
            drive_embed.set_image(url=place.image_url)
        else:
            drive_embed.set_image(url=assets.get_default())
        return drive_embed

    @bot.command(aliases=["here"])
    async def position(ctx):
        if not user_registered(ctx.author.id):
            await ctx.channel.send(
                "{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))
            return

        player = get_player(ctx.author.id)
        place = places.get(player.position)
        position_embed = discord.Embed(title="{}'s Position".format(ctx.author.name),
                                       description="You are at {}".format(player.position),
                                       colour=discord.Colour.gold())
        if place is not None:
            position_embed.add_field(name="What is here?",
                                     value=symbols.LIST_ITEM + place.name, inline=False)
            if len(place.commands[0]) != 0:
                position_embed.add_field(name="Available Commands",
                                         value=get_place_commands(place.commands))
            position_embed.add_field(name="Note", value="The commands don't work yet :(")
            position_embed.set_image(url=place.image_url)
        else:
            position_embed.add_field(name="What is here?", value="Nothing :frowning:", inline=False)
        await ctx.channel.send(embed=position_embed)

    def get_place_commands(command_list):
        readable = ""
        for command in command_list:
            readable = "{}{}`{}`\n".format(readable, symbols.LIST_ITEM, command)
        return readable

    @bot.command(aliases=["places"])
    async def addressbook(ctx):
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.gold())
        for place in places.get_public():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.channel.send(embed=places_embed)

    @bot.command()
    async def job(ctx):
        if not user_registered(ctx.author.id):
            await ctx.channel.send(
                "{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))
            return
        # TODO generate Job
        player = get_player(ctx.author.id)
        job_emded = discord.Embed(title="{}'s Job".format(player.name), colour=discord.Colour.gold())
        await ctx.channel.send(embed=job_emded)


    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def bing(ctx):
        answer = await ctx.channel.send("Bong")
        await ctx.channel.send(str(round((answer.created_at-ctx.message.created_at).total_seconds()*1000))+ "  ms")

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def info(ctx):
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.gold())

        uptime = datetime.now()-start_time
        days = uptime.days
        hours = floor(uptime.seconds/3600)
        minutes = floor(uptime.seconds/60)-hours*60
        seconds = uptime.seconds-hours*3600-minutes*60
        info_embed.add_field(name="Uptime",
                             value="{}d {}h {}m {}s".format(days, hours, minutes, seconds))
        info_embed.add_field(name="Latency", value=str(round(bot.latency, 2)*1000)+" ms")
        cur.execute("SELECT COUNT(*) FROM players")
        info_embed.add_field(name="Registered Players", value=cur.fetchall()[0][0])
        await ctx.channel.send(embed=info_embed)

    @bot.command()
    @commands.is_owner()
    async def adminctl(ctx, *args):
        if not args:
            await ctx.channel.send("Missing arguments")
            return
        if args[0] == "reloadplaces":
            reload(places)
            await ctx.channel.send("Done")

        if args[0] == "shutdown":
            # TODO add scheduling
            # await ctx.channel.send("Are you sure to init the shutdown [y/N]")
            await bot.change_presence(status=discord.Status.idle)
            await ctx.channel.send("Shutting down")
            await bot.logout()

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, discord.ext.commands.errors.BotMissingPermissions):
            missing_permissions = '`'
            for permission in error.missing_perms:
                missing_permissions = missing_permissions + "\n"+ permission
            await ctx.channel.send("I'm missing the following permissions:"+missing_permissions+'`')
        else:
            print(error)

    def user_registered(user_id):
        cur.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
        if len(cur.fetchall()) == 1:
            return True
        return False

    def get_player(user_id):
        cur.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
        return players.from_tuple(cur.fetchone())

    def get_active_drive(player_id, message_id):
        for active_drive in active_drives:
            if active_drive.player.user_id == player_id and active_drive.message.id == message_id:
                return active_drive
        return None

    loop = asyncio.get_event_loop()
    loop.create_task(check_drives())
    start_time = datetime.now()
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()
