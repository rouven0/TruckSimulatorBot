"""
This module contains the Cog for all driving-related commands
"""
from time import time
import asyncio
import discord
from discord.ext import commands
import players
import places
import symbols
import config
import assets
import jobs

class Driving(commands.Cog):
    """
    The heart of the Truck simulator: Drive your Truck on a virtual map
    """
    def __init__(self):
        self.active_drives = []

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        All the driving reactions are processed here
        Only when the stop sign is he reaction emoji, changes will be applied
        """
        if reaction.message.id not in [p.message.id for p in self.active_drives]:
            return
        active_drive = self.get_active_drive(user.id, message_id=reaction.message.id)
        if active_drive is None:
            return
        if active_drive.islocked():
            return

        if reaction.emoji == symbols.STOP:
            self.active_drives.remove(active_drive)
            await reaction.message.clear_reactions()
            await reaction.message.channel.send("You stopped driving!, {}".format(user.name))
            players.update(active_drive.player, position=active_drive.player.position,
                           miles=active_drive.player.miles)

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
            await reaction.message.edit(
                embed=self.get_drive_embed(active_drive.player, user.avatar_url))
            if (active_drive.player.position[0] >= config.MAP_BORDER or
                    active_drive.player.position[1] >= config.MAP_BORDER or
                    active_drive.player.position[0] < 1 or
                    active_drive.player.position[1] < 1):
                await reaction.message.clear_reactions()
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
            active_drive.unlock()


    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def drive(self, ctx):
        """
        Start driving your Truck on the map and control it with reactions
        """
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return

        if ctx.author.id in [a.player.user_id for a in self.active_drives]:
            await ctx.channel.send("You can't drive on two roads at once!")
            return

        message = await ctx.channel.send(embed=self.get_drive_embed(player, ctx.author.avatar_url))
        for symbol in symbols.get_drive_position_symbols(player.position):
            await message.add_reaction(symbol)
        self.active_drives.append(players.ActiveDrive(player, message, time()))

    def get_drive_embed(self, player, avatar_url):
        """
        Returns a discord embed with all the information about the current drive
        """
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
            drive_embed.add_field(name="Navigation: Drive to {}".format(navigation_place.name),
                                  value=navigation_place.position)
        if place is not None:
            drive_embed.set_image(url=place.image_url)
        else:
            drive_embed.set_image(url=assets.get_default())
        return drive_embed

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True, manage_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def stop(self, ctx):
        """
        This is an alternate stop method to get your changes applied if there
        is a problem with the reactions
        """
        if not players.registered(ctx.author.id):
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return
        active_drive = self.get_active_drive(ctx.author.id)
        if active_drive is None:
            await ctx.channel.send("Your truck already stopped driving. "
                                   "But you checked the handbrake just to be sure.")
            return
        self.active_drives.remove(active_drive)
        await active_drive.message.clear_reactions()
        await ctx.channel.send("You stopped driving!, {}".format(ctx.author.name))
        players.update(active_drive.player,
                       position=active_drive.player.position,
                       miles=active_drive.player.miles)

    @commands.command(aliases=["here"])
    async def position(self, ctx):
        """
        Provides some information about your current position and the things located there
        """
        player = players.get(ctx.author.id)
        if player is None:
            await ctx.channel.send(
                "{} you are not registered yet! "
                "Try `t.register` to get started".format(ctx.author.mention))
            return

        place = places.get(player.position)
        position_embed = discord.Embed(description="You are at {}".format(player.position),
                                       colour=discord.Colour.gold())
        position_embed.set_author(name="{}'s Position".format(ctx.author.name),
                                  icon_url=ctx.author.avatar_url)
        if place is not None:
            position_embed.add_field(name="What is here?",
                                     value=symbols.LIST_ITEM + place.name, inline=False)
            if len(place.commands[0]) != 0:
                position_embed.add_field(name="Available Commands",
                                         value=self.get_place_commands(place.commands))
            position_embed.add_field(name="Note", value="The commands don't work yet :(")
            position_embed.set_image(url=place.image_url)
        else:
            position_embed.add_field(name="What is here?", value="Nothing :frowning:", inline=False)
        await ctx.channel.send(embed=position_embed)

    def get_place_commands(self, command_list):
        """
        Returns a string in which all available commands for this place are listed
        """
        readable = ""
        for command in command_list:
            readable = "{}{}`{}`\n".format(readable, symbols.LIST_ITEM, command)
        return readable

    @commands.command(aliases=["places"])
    async def addressbook(self, ctx):
        """
        Lists all public places. Hidden ones are excluded
        """
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.gold())
        for place in places.get_public():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.channel.send(embed=places_embed)


    def get_active_drive(self, player_id, message_id=None):
        """
        Returns an ActiveDrive object for a specific player and message
        """
        if message_id is not None:
            for drv in self.active_drives:
                if drv.player.user_id == player_id and drv.message.id == message_id:
                    return drv
            return None

        for drv in self.active_drives:
            if drv.player.user_id == player_id:
                return drv
        return None

    async def check_drives(self):
        """
        Drives that are inactive for more than 10 minutes get stopped
        """
        while True:
            for drv in self.active_drives:
                if time() - drv.last_action_time > 600:
                    self.active_drives.remove(drv)
                    await drv.message.clear_reactions()
                    await drv.message.channel.send("<@{}> Your driving timed out!".format(drv.player.user_id))
                    players.update(drv.player, position=drv.player.position, miles=drv.player.miles)
            await asyncio.sleep(10)

    async def on_shutdown(self):
        """
        Stop all drivings and save changes to the database when the bot is shut down
        """
        processed_channels = []
        for drv in self.active_drives:
            self.active_drives.remove(drv)
            await drv.message.clear_reactions()
            if drv.message.channel.id not in processed_channels:
                await drv.message.channel.send("All trucks were stopped due to a bot shutdown!")
                processed_channels.append(drv.message.channel.id)
            players.update(drv.player, position=drv.player.position, miles=drv.player.miles)
