import sqlite3
from time import time
from os import getenv
from datetime import datetime
from random import randint
from math import floor, sqrt
from importlib import reload
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

import assets
import config
# import help
import items
import jobs
import players
import places
import symbols

load_dotenv('./.env')
# BOT_TOKEN = getenv('BOT_TOKEN')
BOT_PREFIX = getenv('BOT_PREFIX').split(";")

# Alternate token and prefix for testing. Uncomment if needed
# remove this if the bot is transferred to a remote server, only the real token will be stored then
BOT_TOKEN = getenv('TEST_BOT_TOKEN')
# BOT_PREFIX = getenv('TEST_BOT_PREFIX').split(";")


def main():
    con = sqlite3.connect('players.db')
    cur = con.cursor()
    bot = commands.Bot(command_prefix=BOT_PREFIX,
                       help_command=commands.DefaultHelpCommand(),
                       case_insensitive=True)
    active_drives = []

    @bot.event
    async def on_ready():
        print("Connected to Discord")
        await bot.change_presence(status=discord.Status.online,
                                  activity=discord.Activity(
                                      type=discord.ActivityType.watching,
                                      name=str(len(bot.guilds)) + " Servers"))
        print("Bot servers:")
        for guild in bot.guilds:
            print(guild.name)

    @bot.event
    async def on_reaction_add(reaction, user):
        """
        This method is only used to process the driving
        """
        if reaction.message.id not in [p.message.id for p in active_drives]:
            return
        active_drive = get_active_drive(user.id, message_id=reaction.message.id)
        if active_drive is None:
            return
        if active_drive.islocked():
            return

        if reaction.emoji == symbols.STOP:
            active_drives.remove(active_drive)
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
            active_drive.lock()
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
            # add optional sleep to prevent rate limits
            # await asyncio.sleep(1)
            active_drive.unlock()

    async def check_drives():
        while True:
            for drv in active_drives:
                if time() - drv.last_action_time > 600:
                    active_drives.remove(drv)
                    await drv.message.clear_reactions()
                    await drv.message.channel.send("<@{}> Your driving timed out!".format(drv.player.user_id))
                    cur.execute("UPDATE players SET position=? WHERE id=?",
                                (players.format_pos_to_db(drv.player.position), drv.player.user_id))
                    cur.execute("UPDATE players SET miles=? WHERE id=?",
                                (drv.player.miles, drv.player.user_id))
                    con.commit()
            await asyncio.sleep(10)

    @bot.command()
    async def treasure(ctx):
        player = get_player(ctx.author.id)
        if player is None:
            return
        if player.position in [pl.position for pl in places.get_hidden()]:
            cur.execute('UPDATE players SET money=50000 WHERE id=?', ctx.author.id)
            cur.execute('UPDATE players SET position=? WHERE id=?', ("0/0", ctx.author.id))
            con.commit()
            await ctx.channel.send("You found a strange chest with 50000 dollars inside. "
                                   "Then you woke up at 0/0")
            tempcon = sqlite3.connect('objects.db')
            tempcur = tempcon.cursor()
            tempcur.execute('DELETE FROM places WHERE position=?', '1000/1000')
            tempcon.commit()
            tempcon.close()
            reload(places)

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def register(ctx):
        # id, name, money, position, quest_id, miles
        if not user_registered(ctx.author.id):
            cur.execute("INSERT INTO players VALUES (?,?,?,?,?)",
                        (ctx.author.id, ctx.author.name, 0, "0/0", 0))
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

        player = get_player(requested_id)
        if player is None:
            await ctx.channel.send("<@!{}> is not registered yet! "
                                   "Try `t.register` to get started".format(requested_id))
            return

        current_job = get_job(ctx.author.id)
        profile_embed = discord.Embed(title="{}'s Profile".format(player.name),
                                      colour=discord.Colour.gold())
        profile_embed.add_field(name="Money", value=player.money)
        profile_embed.add_field(name="Miles driven", value=player.miles, inline=False)
        if current_job is not None:
            profile_embed.add_field(name="Current Job", value=show_job(current_job))
            await ctx.channel.send(embed=profile_embed)

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
            if request == "money":
                val = player.money
            else:
                val = player.miles

            count += 1
            top_body = "{}**{}**. {} - {} {}\n".format(top_body, count, player.name, val, request)
        top_emded = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())
        top_emded.add_field(name="Top {}".format(request), value=top_body)
        await ctx.channel.send(embed=top_emded)

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def drive(ctx):
        player = get_player(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return

        if ctx.author.id in [a.player.user_id for a in active_drives]:
            await ctx.channel.send("You can't drive on two roads at once!")
            return

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

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def stop(ctx):
        if not user_registered(ctx.author.id):
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return
        active_drive = get_active_drive(ctx.author.id)
        if active_drive is None:
            await ctx.channel.send("Your truck already stopped driving. "
                                   "But you checked the handbrake just to be sure.")
            return
        active_drives.remove(active_drive)
        await active_drive.message.clear_reactions()
        await ctx.channel.send("You stopped driving!, {}".format(ctx.author.name))
        cur.execute("UPDATE players SET position=? WHERE id=?",
                    (players.format_pos_to_db(active_drive.player.position), ctx.author.id))
        cur.execute("UPDATE players SET miles=? WHERE id=?",
                    (active_drive.player.miles, ctx.author.id))
        con.commit()

    @bot.command(aliases=["here"])
    async def position(ctx):
        player = get_player(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return

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
        player = get_player(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return
        current_job = get_job(ctx.author.id)
        job_embed = discord.Embed(title=f"{player.name}'s Job", colour=discord.Colour.gold())
        if current_job is None:
            job_tuple=generate_job(player)
            job_embed.add_field(name="You got a new Job", value=job_tuple[1], inline=False)
            job_embed.add_field(name="Current state", value=get_job_state(job_tuple[0]))
        else:
            job_embed.add_field(name="Your current job", value=show_job(current_job), inline=False)
            job_embed.add_field(name="Current state", value=get_job_state(current_job))
        await ctx.channel.send(embed=job_embed)

    def show_job(job: jobs.Job):
        place_from = job.place_from
        place_to = job.place_to
        item = items.get(place_from.produced_item)
        return "Bring {} {} from {} to {}.".format(item.emoji, item.name, place_from.name, place_to.name)

    def generate_job(player: players.Player):
        available_places = places.get_quest_active().copy()
        place_from = available_places[randint(0, len(available_places) - 1)]
        item = items.get(place_from.produced_item)
        available_places.remove(place_from)
        place_to = available_places[randint(0, len(available_places) - 1)]
        miles_x = abs(place_from.position[0] - place_to.position[0])
        miles_y = abs(place_from.position[1] - place_to.position[1])
        reward = round(sqrt(miles_x**2 + miles_y**2)*37)
        new_job = jobs.Job(player.user_id, place_from, place_to, 0, reward)
        cur.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', jobs.to_tuple(new_job))
        con.commit()
        return (new_job , "{} needs {} {} from {}. You get ${} for this transport".format(place_to.name,
            item.emoji, item.name, place_from.name, reward))

    def get_job_state(job: jobs.Job):
        if job.state == 0:
            return "You claimed this job. Drive to {} and load your truck".format(job.place_from.name)
        if job.state == 1:
            return "You loaded your truck with the needed items. Now drive to {} and unload them".format(job.place_to.name)
        if job.state == 2:
            return "Your job is done. If you can read this, something went wrong"

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def bing(ctx):
        answer = await ctx.channel.send("Bong")
        await ctx.channel.send(str(round((answer.created_at - ctx.message.created_at).total_seconds() * 1000)) + "ms")

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def info(ctx):
        info_embed = discord.Embed(title="Truck Simulator info", colour=discord.Colour.gold())

        uptime = datetime.now() - start_time
        days = uptime.days
        hours = floor(uptime.seconds / 3600)
        minutes = floor(uptime.seconds / 60) - hours * 60
        seconds = uptime.seconds - hours * 3600 - minutes * 60
        info_embed.add_field(name="Uptime",
                             value="{}d {}h {}m {}s".format(days, hours, minutes, seconds))
        info_embed.add_field(name="Latency", value=str(round(bot.latency, 2) * 1000) + " ms")
        cur.execute("SELECT COUNT(*) FROM players")
        info_embed.add_field(name="Registered Players", value=cur.fetchall()[0][0])
        info_embed.add_field(name="Servers", value=len(bot.guilds))
        await ctx.channel.send(embed=info_embed)

    @bot.command()
    @commands.is_owner()
    async def adminctl(ctx, *args):
        if not args:
            await ctx.channel.send("Missing arguments")
            return
        if args[0] == "reloadplaces":
            reload(places)
            reload(items)
            await ctx.channel.send("Done")

        if args[0] == "shutdown":
            # await ctx.channel.send("Are you sure to init the shutdown [y/N]")
            await bot.change_presence(status=discord.Status.idle)
            await ctx.channel.send("Shutting down")
            await bot.logout()

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.BotMissingPermissions):
            missing_permissions = '`'
            for permission in error.missing_perms:
                missing_permissions = missing_permissions + "\n" + permission
            await ctx.channel.send("I'm missing the following permissions:" + missing_permissions + '`')
        else:
            print(error)

    def user_registered(user_id):
        cur.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
        if len(cur.fetchall()) == 1:
            return True
        return False

    def get_player(user_id):
        cur.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
        try:
            return players.from_tuple(cur.fetchone())
        except TypeError:
            return None

    def get_job(user_id):
        cur.execute("SELECT * FROM jobs WHERE player_id=:id", {"id": user_id})
        try:
            return jobs.from_tuple(cur.fetchone())
        except TypeError:
            return None

    def get_active_drive(player_id, message_id=None):
        if message_id is not None:
            for drv in active_drives:
                if drv.player.user_id == player_id and drv.message.id == message_id:
                    return drv
            return None

        for drv in active_drives:
            if drv.player.user_id == player_id:
                return drv
        return None

    loop = asyncio.get_event_loop()
    loop.create_task(check_drives())
    start_time = datetime.now()
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()
