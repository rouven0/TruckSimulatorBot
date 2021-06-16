"""
This module contains the Cog for all driving-related commands
"""
from time import time
import asyncio
import discord
from discord.ext import commands
from discord_components import Button, Interaction
import players
import items
import places
import symbols
import assets
import jobs


def generate_minimap(player) -> str:
    """
    This generate the minimap shown in t.drive
    """
    minimap_array = []
    for i in range(0,7):
        minimap_array.append([])
        for j in range(0,7):
            minimap_array[i].append("")
            map_place = places.get([player.position[0]-3+j, player.position[1]+3-i])
            try:
                minimap_array[i][j]=items.get(map_place.produced_item).emoji
            except AttributeError:
                minimap_array[i][j] = ":black_large_square:"

    minimap_array[3][3] = ":truck:"
    minimap = ""
    for i in range(0,7):
        for j in range(0, 7):
            minimap = minimap + minimap_array[i][j]
        minimap = minimap + "\n"
    return minimap


def get_drive_embed(player, avatar_url) -> discord.Embed:
    """
    Returns a discord embed with all the information about the current drive
    """
    place = places.get(player.position)
    drive_embed = discord.Embed(description="We hope he has fun",
                                colour=discord.Colour.gold())
    drive_embed.set_author(name="{} is driving".format(player.name), icon_url=avatar_url)
    drive_embed.add_field(name="Minimap", value=generate_minimap(player), inline=False)
    drive_embed.add_field(name="Position", value=player.position)
    current_job = jobs.get(player.user_id)
    if current_job is not None:
        if current_job.state == 0:
            navigation_place = current_job.place_from
        else:
            navigation_place = current_job.place_to
        drive_embed.add_field(name="Navigation: Drive to {}".format(navigation_place.name),
                              value=navigation_place.position)
    if place.image_url is not None:
        drive_embed.set_image(url=place.image_url)
    else:
        drive_embed.set_image(url=assets.get_default())
    drive_embed.set_footer(text="Note: Your position is only applied if you stop driving")
    return drive_embed

class Driving(commands.Cog):
    """
    The heart of the Truck simulator: Drive your Truck on a virtual map
    """

    def __init__(self, bot):
        self.bot = bot
        self.active_drives = []


    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):
        """
        All the driving reactions are processed here
        Only when the stop sign is he reaction emoji, changes will be applied
        i
        """
        if isinstance(interaction.component, list):
            # Return if buttons are clicked too fast
            await interaction.respond(type=6)
            return
        active_drive = self.get_active_drive(interaction.author.id, message_id=interaction.message.id)
        if active_drive is None:
            # Return if the wrong player clicked the button
            return

        try:
            action = int(interaction.component.emoji.id)
        except AttributeError:
            action = interaction.component.label
        if action == symbols.STOP:
            self.active_drives.remove(active_drive)
            await interaction.message.channel.send("You stopped driving!, {}".format(interaction.author.name))
            await interaction.respond(type=7, components=[])
            players.update(active_drive.player, position=active_drive.player.position,
                           miles=active_drive.player.miles)

        position_changed = False
        if action == symbols.LEFT:
            active_drive.player.position = [active_drive.player.position[0] - 1, active_drive.player.position[1]]
            position_changed = True

        if action == symbols.UP:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1] + 1]
            position_changed = True

        if action == symbols.DOWN:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1] - 1]
            position_changed = True

        if action == symbols.RIGHT:
            active_drive.player.position = [active_drive.player.position[0] + 1, active_drive.player.position[1]]
            position_changed = True

        if position_changed:
            active_drive.last_action_time = time()
            active_drive.player.miles += 1
            buttons = []
            for symbol in symbols.get_drive_position_symbols(active_drive.player.position):
                buttons.append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbol)))
            buttons.append(Button(style=4, label=" ", emoji=self.bot.get_emoji(symbols.STOP)))

            await interaction.message.edit(embed=get_drive_embed(active_drive.player,
                                                                      interaction.author.avatar_url),
                                           components=[buttons])
            await interaction.respond(type=7)


    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def drive(self, ctx):
        """
        Start driving your Truck on the map and control it with reactions
        """
        player = players.get(ctx.author.id)
        if ctx.author.id in [a.player.user_id for a in self.active_drives]:
            await ctx.channel.send("You can't drive on two roads at once!")
            return
        buttons = []
        for symbol in symbols.get_drive_position_symbols(player.position):
            buttons.append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbol)))
        buttons.append(Button(style=4, label=" ", emoji=self.bot.get_emoji(symbols.STOP)))
        message = await ctx.channel.send(embed=get_drive_embed(player, ctx.author.avatar_url),
                                         components=[buttons])
        self.active_drives.append(players.ActiveDrive(player, message, time()))




    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def stop(self, ctx):
        """
        This is an alternate stop method to get your changes applied if there
        is a problem with the reactions
        """
        active_drive = self.get_active_drive(ctx.author.id)
        if active_drive is None:
            await ctx.channel.send("Nothing to do here")
            return
        self.active_drives.remove(active_drive)
        await active_drive.message.edit(
            embed=get_drive_embed(active_drive.player, ctx.author.avatar_url), components=[])
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
        place = places.get(player.position)
        position_embed = discord.Embed(description="You are at {}".format(player.position),
                                       colour=discord.Colour.gold())
        position_embed.set_author(name="{}'s Position".format(ctx.author.name),
                                  icon_url=ctx.author.avatar_url)
        position_embed.add_field(name="What is here?",
                                 value=symbols.LIST_ITEM + place.name, inline=False)
        if len(place.commands) != 0 and len(place.commands[0]) != 0:
            position_embed.add_field(name="Available Commands",
                                     value=self.get_place_commands(place.commands))
        if place.image_url is not None:
            position_embed.set_image(url=place.image_url)
        await ctx.channel.send(embed=position_embed)


    @staticmethod
    def get_place_commands(command_list):
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
            for active_drive in self.active_drives:
                if active_drive.player.user_id == player_id and active_drive.message.id == message_id:
                    return active_drive
            return None

        for active_drive in self.active_drives:
            if active_drive.player.user_id == player_id:
                return active_drive
        return None


    async def check_drives(self):
        """
        Drives that are inactive for more than 10 minutes get stopped
        """
        while True:
            for active_drive in self.active_drives:
                if time() - active_drive.last_action_time > 600:
                    self.active_drives.remove(active_drive)
                    await active_drive.message.edit(
                        embed=get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[])
                    await active_drive.message.channel.send(
                        "<@{}> Your driving timed out!".format(active_drive.player.user_id))
                    players.update(active_drive.player, position=active_drive.player.position,
                                   miles=active_drive.player.miles)
            await asyncio.sleep(10)


    async def on_shutdown(self):
        """
        Stop all drivings and save changes to the database when the bot is shut down
        """
        processed_channels = []
        for active_drive in self.active_drives:
            self.active_drives.remove(active_drive)
            await active_drive.message.edit(
                embed=get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[])
            if active_drive.message.channel.id not in processed_channels:
                await active_drive.message.channel.send("All trucks were stopped due to a bot shutdown!")
                processed_channels.append(active_drive.message.channel.id)
            players.update(active_drive.player, position=active_drive.player.position, miles=active_drive.player.miles)
