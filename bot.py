import os
import sqlite3
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
BOT_TOKEN = os.getenv('BOT_TOKEN')


def main():
    con = sqlite3.connect('players.db')
    cur = con.cursor()
    bot = commands.Bot(command_prefix=["t.", "T."], help_command=discord.ext.commands.DefaultHelpCommand(),
                       case_insensitive=True)
    active_drives = []

    @bot.event
    async def on_ready():
        print("Connected to Discord")
        await bot.change_presence(status=discord.Status.online,
                                  activity=discord.Activity(type=discord.ActivityType.watching, name="the hills passing by"))

    @bot.event
    async def on_reaction_add(reaction, user):
        """
        This method is only used to process the driving
        """
        #TODO add timeouts
        if reaction.message.id not in [p.message.id for p in active_drives]:
            return
        active_drive = get_active_drive(user.id)
        if active_drive is None:
            return

        if reaction.emoji == symbols.STOP:
            active_drives.remove(get_active_drive(user.id))
            await reaction.message.clear_reactions()
            await reaction.message.channel.send("You stopped driving!, {}".format(user.name))
            cur.execute("UPDATE players SET position=? WHERE id=?",
                        (players.format_pos_to_db(active_drive.player.position), user.id))
            cur.execute("UPDATE players SET miles=? WHERE id=?", (active_drive.player.miles, user.id))
            con.commit()

        position_changed = False
        if reaction.emoji == symbols.LEFT:
            active_drive.player.position = [active_drive.player.position[0] - 1, active_drive.player.position[1]]
            position_changed = True

        if reaction.emoji == symbols.UP:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1] + 1]
            position_changed = True

        if reaction.emoji == symbols.DOWN:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1] - 1]
            position_changed = True

        if reaction.emoji == symbols.RIGHT:
            active_drive.player.position = [active_drive.player.position[0] + 1, active_drive.player.position[1]]
            position_changed = True

        if position_changed:
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

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def register(ctx):
        if not user_registered(ctx.author.id):
            cur.execute("INSERT INTO players VALUES (?,?,?,?,?,?)", (ctx.author.id, ctx.author.name, 0, 0, "0/0", 0))
            con.commit()
            print("{} got registered".format(ctx.author.name))
            await ctx.channel.send("Welcome to the Truckers, {}".format(ctx.author.mention))
        else:
            await ctx.channel.send("You are already registered")

    @bot.command(aliases=["p", "me"])
    async def profile(ctx, *args):
        if args and args[0].startswith("<@"):
            requested_id = int(args[0][args[0].find("@") + 1:args[0].find(">")])
        else:
            requested_id = ctx.author.id

        if user_registered(requested_id):
            player = get_player(requested_id)
            profile_embed = discord.Embed(title="{}'s Profile".format(player.name), colour=discord.Colour.gold())
            profile_embed.add_field(name="Money", value=player.money, inline=False)
            profile_embed.add_field(name="Miles driven", value=player.miles)
            await ctx.channel.send(embed=profile_embed)
        else:
            await ctx.channel.send("<@!{}> is not registered yet! Try `t.register` to get started".format(requested_id))

    @bot.command()
    async def top(ctx):
        cur.execute('SELECT * FROM players ORDER BY miles DESC')
        top_embed = players.list_from_tuples(cur.fetchmany(10))
        top_body = ""
        count = 0
        for player in top_embed:
            count += 1
            top_body = "{}**{}**. {} - {} miles\n".format(top_body, count, player.name, player.miles)
        top_emded = discord.Embed(title="Truck Simulator top list", colour=discord.Colour.gold())
        top_emded.add_field(name="Top miles", value=top_body)
        await ctx.channel.send(embed=top_emded)

    @bot.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def drive(ctx):
        if ctx.author.id in [a.player.user_id for a in active_drives]:
            await ctx.channel.send("You can't drive on two roads at once!")
            return
        if user_registered(ctx.author.id):
            player = get_player(ctx.author.id)
            message = await ctx.channel.send(embed=get_drive_embed(player))
            for symbol in symbols.get_drive_position_symbols(player.position):
                await message.add_reaction(symbol)
            active_drives.append(players.ActiveDrive(player, message))
        else:
            await ctx.channel.send(
                "{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))

    def get_drive_embed(player):
        place = places.get(player.position)
        drive_embed = discord.Embed(title="{} is driving".format(player.name),
                                    description="We hope he has fun",
                                    colour=discord.Colour.gold())
        drive_embed.add_field(name="Instructions",
                              value=open("./drive_instrucions.md", "r").read(),
                              inline=False)
        drive_embed.add_field(name="Note", value="Your position is only applied if you stop driving", inline=False)
        drive_embed.add_field(name="Position", value=player.position)
        if place is not None:
            drive_embed.set_image(url=place.image_url)
        else:
            drive_embed.set_image(url=assets.get_default())
        return drive_embed

    @bot.command(aliases=["here"])
    async def position(ctx):
        if user_registered(ctx.author.id):
            player = get_player(ctx.author.id)
            place = places.get(player.position)
            position_embed = discord.Embed(title="{}'s Position".format(ctx.author.name, colour=discord.Colour.gold()),
                                           description="You are at {}".format(player.position),
                                           colour=discord.Colour.gold())
            if place is not None:
                position_embed.add_field(name="What is here?", value=symbols.LIST_ITEM + place.name, inline=False)
                if len(place.commands[0])!=0:
                    position_embed.add_field(name="Available Commands", value=get_place_commands(place.commands))
                position_embed.add_field(name="Note", value="The commands don't work yet :(")
            else:
                position_embed.add_field(name="What is here?", value="Nothing :frowning:", inline=False)
            await ctx.channel.send(embed=position_embed)
        else:
            await ctx.channel.send(
                "{} you are not registered yet! Try `t.register` to get started".format(ctx.author.mention))

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
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True, embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
    async def bing(ctx):
        await ctx.channel.send("Bong")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, discord.ext.commands.errors.BotMissingPermissions):
            missing_permissions = '`'
            for permission in error.missing_perms:
                missing_permissions = missing_permissions + "\n"+ permission 
            await ctx.channel.send("I'm missing the following permissions:"+ missing_permissions+'`')
        else:
            print(error)

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
