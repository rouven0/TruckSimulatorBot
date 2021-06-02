from time import time
from os import getenv
from datetime import datetime
from math import floor
from importlib import reload
import asyncio
import logging
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
BOT_TOKEN = getenv('BOT_TOKEN')
BOT_PREFIX = getenv('BOT_PREFIX').split(";")

def main():
    bot = commands.Bot(command_prefix=BOT_PREFIX,
                       help_command=commands.DefaultHelpCommand(),
                       case_insensitive=True)
    active_drives = []

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(console_handler)

    file_handler = console_handler = logging.FileHandler("./logs/{}.log".format(datetime.now().strftime("%Y-%m-%d_%H:%M")))
    file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(file_handler)

    @bot.event
    async def on_ready():
        logging.info("Connected to Discord")
        print("ready")
        await bot.change_presence(status=discord.Status.online,
                                  activity=discord.Activity(
                                      type=discord.ActivityType.watching,
                                      name=str(len(bot.guilds)) + " Servers"))

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
            players.update(active_drive.player, position=active_drive.player.position, miles=active_drive.player.miles)

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
            await reaction.message.edit(embed=get_drive_embed(active_drive.player, user.avatar_url))
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
                    players.update(drv.player, position=drv.player.position, miles=drv.player.miles)
            await asyncio.sleep(10)

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def register(ctx):
        if not players.registered(ctx.author.id):
            players.insert(players.Player(ctx.author.id, ctx.author.name))
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

    @bot.command()
    async def top(ctx, *args):
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

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def drive(ctx):
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return

        if ctx.author.id in [a.player.user_id for a in active_drives]:
            await ctx.channel.send("You can't drive on two roads at once!")
            return

        message = await ctx.channel.send(embed=get_drive_embed(player, ctx.author.avatar_url))
        for symbol in symbols.get_drive_position_symbols(player.position):
            await message.add_reaction(symbol)
        active_drives.append(players.ActiveDrive(player, message, time()))

    def get_drive_embed(player, avatar_url):
        place = places.get(player.position)
        drive_embed = discord.Embed(description="We hope he has fun",
                                    colour=discord.Colour.gold())
        drive_embed.set_author(name="{} is driving".format(player.name), icon_url=avatar_url)
        drive_embed.add_field(name="Instructions",
                              value=open("./drive_instrucions.md", "r").read(),
                              inline=False)
        drive_embed.add_field(name="Note",
                              value="Your position is only applied if you stop driving",
                              inline=False)
        drive_embed.add_field(name="Position", value=player.position)
        current_job = jobs.get(player.user_id)
        if current_job is not None:
            if current_job.state == 0:
                navigation_place = current_job.place_from
            else:
                navigation_place = current_job.place_to
            drive_embed.add_field(name="Navigation: Drive to {}".format(navigation_place.name), value=navigation_place.position)
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
        if not players.registered(ctx.author.id):
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
        players.update(active_drive.player, position=active_drive.player.position, miles=active_drive.player.miles)

    @bot.command(aliases=["here"])
    async def position(ctx):
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return

        place = places.get(player.position)
        position_embed = discord.Embed(description="You are at {}".format(player.position),
                                       colour=discord.Colour.gold())
        position_embed.set_author(name="{}'s Position".format(ctx.author.name), icon_url=ctx.author.avatar_url)
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
    async def job(ctx, *args):
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return
        current_job = jobs.get(ctx.author.id)
        job_embed = discord.Embed(colour=discord.Colour.gold())
        job_embed.set_author(name="{}'s Job".format(ctx.author.name), icon_url=ctx.author.avatar_url)
        if current_job is None:
            if args and args[0] == "new":
                job_tuple=jobs.generate(player)
                job_embed.add_field(name="You got a new Job", value=job_tuple[1], inline=False)
                job_embed.add_field(name="Current state", value=jobs.get_state(job_tuple[0]))
            else:
                job_embed.add_field(name="You don't have a job at the moment",
                                    value="Type `t.job new` to get one")
        else:
            job_embed.add_field(name="Your current job", value=jobs.show(current_job), inline=False)
            job_embed.add_field(name="Current state", value=jobs.get_state(current_job))
        await ctx.channel.send(embed=job_embed)

    @bot.command()
    async def load(ctx):
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return
        current_job = jobs.get(ctx.author.id)
        if current_job is None:
            await ctx.channel.send("Nothing to do here")
            return
        if player.position == current_job.place_from.position:
            current_job.state = 1
            await ctx.channel.send(jobs.get_state(current_job))
            jobs.update(current_job, state=current_job.state)
        else:
            await ctx.channel.send("Nothing to do here")

    @bot.command()
    async def unload(ctx):
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return
        current_job = jobs.get(ctx.author.id)
        if current_job is None:
            await ctx.channel.send("Nothing to do here")
            return
        if player.position == current_job.place_to.position and current_job.state == 1:
            current_job.state = 2
            await ctx.channel.send(jobs.get_state(current_job))
            jobs.remove(current_job)
            players.update(player, money=player.money+current_job.reward)
        else:
            await ctx.channel.send("Nothing to do here")

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
        info_embed.add_field(name="Registered Players", value=players.get_count())
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
            processed_channels = []
            for drv in active_drives:
                active_drives.remove(drv)
                await drv.message.clear_reactions()
                if drv.message.channel.id not in processed_channels:
                    await drv.message.channel.send("All trucks were stopped due to a bot shutdown!")
                    processed_channels.append(drv.message.channel.id)
                players.update(drv.player, position=drv.player.position, miles=drv.player.miles)
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
