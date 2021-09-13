"""
This module contains the Cog for all driving-related commands
"""
import asyncio
from datetime import datetime
from time import time
from typing import Union

import discord
from discord.asset import Asset
from discord.ext import commands
from discord.ext import tasks
from discord_slash import cog_ext
from discord_slash.utils.manage_components import (
    create_button,
    create_actionrow,
    create_select,
    create_select_option,
    ComponentContext,
    wait_for_component,
)
import api.players as players
import api.items as items
import api.levels as levels
import api.places as places
import api.symbols as symbols
import api.assets as assets
import api.jobs as jobs
import api.trucks as trucks


class Driving(commands.Cog):
    """
    The heart of the Truck simulator: Drive your Truck on a virtual map
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active_drives = []
        super().__init__()

    def get_buttons(self, player: players.Player) -> list:
        """
        Returns buttons based on the players position
        """
        buttons = []
        directional_buttons = []
        place = places.get(player.position)
        for symbol in symbols.get_all_drive_symbols():
            if symbol in symbols.get_drive_position_symbols(player.position):
                directional_buttons.append(
                    create_button(style=1, emoji=self.bot.get_emoji(symbol), custom_id=str(symbol))
                )
            else:
                directional_buttons.append(create_button(style=1, emoji=self.bot.get_emoji(symbol), disabled=True))
        directional_buttons.append(create_button(style=4, emoji=self.bot.get_emoji(symbols.STOP), custom_id="stop"))
        buttons.append(create_actionrow(*directional_buttons))
        current_job = jobs.get(player.user_id)
        action_buttons = []
        load_disabled = not (len(player.loaded_items) < trucks.get(player.truck_id).loading_capacity)
        unload_disabled = not (len(player.loaded_items) > 0)
        if place.name == "Nothing":
            load_disabled = True
            unload_disabled = True

        action_buttons.append(
            create_button(style=1, emoji=self.bot.get_emoji(symbols.LOAD), custom_id="load", disabled=load_disabled)
        )
        action_buttons.append(
            create_button(
                style=1, emoji=self.bot.get_emoji(symbols.UNLOAD), custom_id="unload", disabled=unload_disabled
            )
        )

        if player.position == [7, 7]:
            action_buttons.append(create_button(style=2, emoji=self.bot.get_emoji(symbols.REFILL), custom_id="refill"))
        buttons.append(create_actionrow(*action_buttons))
        buttons.append(
            create_actionrow(
                create_button(style=3, label="New Job", custom_id="new_job", disabled=(current_job is not None)),
                create_button(style=2, label="Show Job", custom_id="show_job", disabled=(current_job is None)),
            )
        )
        return buttons

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.check_drives.start()

    @cog_ext.cog_component()
    async def stop(self, ctx: ComponentContext):
        active_drive = self.get_active_drive(ctx.author.id, message_id=ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return

        self.active_drives.remove(active_drive)
        await ctx.edit_origin(components=[])
        await ctx.send("You stopped driving!, {}".format(ctx.author.name))

    @cog_ext.cog_component()
    async def load(self, ctx: ComponentContext):
        active_drive = self.get_active_drive(ctx.author.id, message_id=ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return

        item = items.get(places.get(active_drive.player.position).produced_item)
        await players.load_item(active_drive.player, item)
        job_message = None

        current_job = jobs.get(ctx.author.id)
        if current_job is not None and item.name == current_job.place_from.produced_item:
            current_job.state = jobs.STATE_LOADED
            job_message = jobs.get_state(current_job)
            jobs.update(current_job, state=current_job.state)

        drive_embed = self.get_drive_embed(active_drive.player, ctx.author.avatar_url)
        drive_embed.add_field(
            name="Loading successful",
            value=f"You loaded {self.bot.get_emoji(item.emoji)} {item.name} into your truck",
            inline=False,
        )
        # This order is required to fit the navigation to the right place
        await ctx.edit_origin(embed=drive_embed, components=self.get_buttons(active_drive.player))
        if job_message is not None:
            await ctx.send(
                embed=discord.Embed(title="Job Notification", description=job_message, colour=discord.Colour.gold()),
                hidden=True,
            )

    @cog_ext.cog_component()
    async def unload(self, ctx: ComponentContext):
        active_drive = self.get_active_drive(ctx.author.id, message_id=ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return

        drive_embed = self.get_drive_embed(active_drive.player, ctx.author.avatar_url)
        item_options = []
        for item in active_drive.player.loaded_items:
            # add the item if it doesn't already is in the list
            if item.name not in [o["value"] for o in item_options]:
                item_options.append(
                    create_select_option(label=item.name, value=item.name, emoji=self.bot.get_emoji(item.emoji))
                )
        select = create_select(
            placeholder="Choose which items to unload",
            options=item_options,
            min_values=1,
            max_values=len(item_options),
        )
        cancel_button = create_button(custom_id="cancel", label="Cancel", style=4)
        await ctx.edit_origin(embed=drive_embed, components=[create_actionrow(select), create_actionrow(cancel_button)])
        try:
            item_string = ""
            selection_ctx: ComponentContext = await wait_for_component(self.bot, components=select, timeout=30)
            for name in selection_ctx.selected_options:
                item = items.get(name)
                await players.unload_item(active_drive.player, item)
                if name == selection_ctx.selected_options[0]:
                    item_string += f"{self.bot.get_emoji(item.emoji)} {item.name}"
                elif name == selection_ctx.selected_options[-1]:
                    item_string += f" and {self.bot.get_emoji(item.emoji)} {item.name}"
                else:
                    item_string += f", {self.bot.get_emoji(item.emoji)} {item.name}"
            drive_embed = self.get_drive_embed(active_drive.player, ctx.author.avatar_url)

            current_job = jobs.get(ctx.author.id)
            drive_embed.add_field(
                name="Unloading successful", value=f"You removed {item_string} from your truck", inline=False
            )
            if (
                current_job is not None
                and current_job.place_from.produced_item in selection_ctx.selected_options
                and active_drive.player.position == current_job.place_to.position
            ):
                current_job.state = jobs.STATE_DONE
                await players.add_money(active_drive.player, current_job.reward)
                jobs.remove(current_job)
                job_message = jobs.get_state(current_job) + await players.add_xp(
                    active_drive.player, levels.get_job_reward_xp(active_drive.player.level)
                )
                # get the drive embed egain to fit the job update
                drive_embed = self.get_drive_embed(active_drive.player, ctx.author.avatar_url)
                await ctx.send(
                    embed=discord.Embed(
                        title="Job Notification", description=job_message, colour=discord.Colour.gold()
                    ),
                    hidden=True,
                )
            await selection_ctx.edit_origin(embed=drive_embed, components=self.get_buttons(active_drive.player))
        except asyncio.exceptions.TimeoutError:
            pass

    @cog_ext.cog_component()
    async def cancel(self, ctx: ComponentContext):
        active_drive = self.get_active_drive(ctx.author.id, message_id=ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return
        await ctx.edit_origin(
            embed=self.get_drive_embed(active_drive.player, ctx.author.avatar_url),
            components=self.get_buttons(active_drive.player),
        )

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext) -> None:
        """
        This method is only used to process the directional_buttons for the driving
        """
        active_drive = self.get_active_drive(ctx.author_id, message_id=ctx.origin_message_id)
        try:
            direction = int(ctx.custom_id)
        except ValueError:
            return

        if active_drive is None and direction in symbols.get_all_drive_symbols():
            # Return if the wrong player clicked the button
            await ctx.defer(ignore=True)
            return
        if active_drive is None:
            return

        if direction == symbols.LEFT:
            active_drive.player.position = [active_drive.player.position[0] - 1, active_drive.player.position[1]]

        if direction == symbols.UP:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1] + 1]

        if direction == symbols.DOWN:
            active_drive.player.position = [active_drive.player.position[0], active_drive.player.position[1] - 1]

        if direction == symbols.RIGHT:
            active_drive.player.position = [active_drive.player.position[0] + 1, active_drive.player.position[1]]

        active_drive.last_action_time = time()
        active_drive.player.miles += 1
        active_drive.player.truck_miles += 1
        active_drive.player.gas -= trucks.get(active_drive.player.truck_id).gas_consumption
        if 60 < active_drive.player.gas < 70:
            await ctx.send("You are running out of gas. Please drive to the nearest gas station", hidden=True)

        if active_drive.player.gas <= 0:
            await ctx.edit_origin(components=[])
            await ctx.send(
                "You messed up and ran out of gas. "
                "The company had to have your truck towed away. You will pay $3000 for this incident!"
            )
            try:
                await players.debit_money(active_drive.player, 3000)
            except players.NotEnoughMoney:
                await ctx.send("You are lucky that you don't have enough money. I'll let you go, for now...")
            await players.update(
                active_drive.player, gas=trucks.get(active_drive.player.truck_id).gas_capacity, position=[7, 7]
            )
            self.active_drives.remove(active_drive)
            return

        await ctx.edit_origin(
            embed=self.get_drive_embed(active_drive.player, ctx.author.avatar_url),
            components=self.get_buttons(active_drive.player),
        )

        await players.update(
            active_drive.player,
            position=active_drive.player.position,
            miles=active_drive.player.miles,
            truck_miles=active_drive.player.truck_miles,
            gas=active_drive.player.gas,
        )

    @cog_ext.cog_slash()
    async def drive(self, ctx) -> None:
        """
        Start driving your Truck on the map and control it with buttons
        """
        player = await players.get(ctx.author.id)
        # Detect, when the player is renamed
        if player.name != ctx.author.name:
            await players.update(player, name=ctx.author.name)
        active_drive = self.get_active_drive(ctx.author.id)
        # TODO rework active drive and make exceptions
        if active_drive is not None:
            active_drive = self.get_active_drive(ctx.author.id)
            await ctx.send(
                embed=discord.Embed(
                    title=f"Hey {ctx.author.name}",
                    description="You can't drive on two roads at once!\n"
                    f"Click [here]({active_drive.message.jump_url}) to jump right back into your Truck",
                    colour=discord.Colour.gold(),
                )
            )
        else:
            message = await ctx.send(
                embed=self.get_drive_embed(player, ctx.author.avatar_url), components=self.get_buttons(player)
            )
            self.active_drives.append(players.ActiveDrive(player, message, time()))

    @cog_ext.cog_slash()
    async def position(self, ctx) -> None:
        """
        Provides some information about your current position and the things located there
        """
        player = await players.get(ctx.author.id)
        place = places.get(player.position)
        position_embed = discord.Embed(
            description="You are at {}".format(player.position), colour=discord.Colour.gold()
        )
        position_embed.set_author(name="{}'s Position".format(ctx.author.name), icon_url=ctx.author.avatar_url)
        position_embed.add_field(name="What is here?", value=symbols.LIST_ITEM + place.name, inline=False)
        if len(place.commands) != 0 and len(place.commands[0]) != 0:
            position_embed.add_field(name="Available Commands", value=self.get_place_commands(place.commands))
        if place.image_url_default is not None:
            position_embed.set_image(url=assets.get_place_image(player, place))
        await ctx.send(embed=position_embed)

    @staticmethod
    def get_place_commands(command_list) -> str:
        """
        Returns a string in which all available commands for this place are listed
        """
        readable = ""
        for command in command_list:
            readable = "{}{}`{}`\n".format(readable, symbols.LIST_ITEM, command)
        return readable

    @cog_ext.cog_slash()
    async def addressbook(self, ctx) -> None:
        """
        Lists all public places. Hidden ones are excluded
        """
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.gold())
        for place in places.get_public():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.send(embed=places_embed)

    def get_drive_embed(self, player: players.Player, avatar_url: Asset) -> discord.Embed:
        """
        Returns the drive embed that includes all the information about the current position and gas
        """
        place = places.get(player.position)
        drive_embed = discord.Embed(
            description="Now with slash commands!", colour=discord.Colour.gold(), timestamp=datetime.utcnow()
        )
        drive_embed.set_author(name="{} is driving".format(player.name), icon_url=avatar_url)

        drive_embed.add_field(name="Minimap", value=self.generate_minimap(player), inline=False)
        drive_embed.add_field(name="Position", value=str(player.position))
        drive_embed.add_field(name="Gas left", value=f"{player.gas} l")

        current_job = jobs.get(player.user_id)
        if current_job is not None:
            if current_job.state == 0:
                navigation_place = current_job.place_from
            else:
                navigation_place = current_job.place_to
            drive_embed.add_field(
                name="Navigation: Drive to {}".format(navigation_place.name), value=str(navigation_place.position)
            )

        if place.image_url_default is not None:
            drive_embed.add_field(
                name="What is here?",
                value=f"{self.bot.get_emoji(items.get(place.produced_item).emoji)} {place.name}",
                inline=False,
            )
            drive_embed.set_image(url=assets.get_place_image(player, place))
        else:
            drive_embed.set_image(url=assets.get_default(player))
        drive_embed.set_footer(
            text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}"
        )
        return drive_embed

    def generate_minimap(self, player: players.Player) -> str:
        """
        This generate the minimap shown in t.drive
        """
        minimap_array = []
        for i in range(0, 7):
            minimap_array.append([])
            for j in range(0, 7):
                minimap_array[i].append("")
                position = [player.position[0] - 3 + j, player.position[1] + 3 - i]
                map_place = places.get(position)
                try:
                    item = items.get(map_place.produced_item)
                except items.ItemNotFound:
                    item = None
                if item is not None:
                    minimap_array[i][j] = str(self.bot.get_emoji(items.get(map_place.produced_item).emoji))
                elif position in (a.player.position for a in self.active_drives):
                    for active_drive in self.active_drives:
                        if active_drive.player.position == position:
                            minimap_array[i][j] = trucks.get(active_drive.player.truck_id).emoji
                else:
                    minimap_array[i][j] = symbols.MAP_BACKGROUND

        minimap_array[3][3] = trucks.get(player.truck_id).emoji
        minimap = ""
        for i in range(0, 7):
            for j in range(0, 7):
                minimap = minimap + minimap_array[i][j]
            minimap = minimap + "\n"
        return minimap

    def get_active_drive(self, player_id, message_id=None) -> Union[players.ActiveDrive, None]:
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

    @tasks.loop(seconds=20)
    async def check_drives(self) -> None:
        """
        Drives that are inactive for more than 10 minutes get stopped
        """
        for active_drive in self.active_drives:
            if time() - active_drive.last_action_time > 600:
                self.active_drives.remove(active_drive)
                await players.update(
                    active_drive.player,
                    position=active_drive.player.position,
                    miles=active_drive.player.miles,
                    truck_miles=active_drive.player.truck_miles,
                    gas=active_drive.player.gas,
                )
                await active_drive.message.edit(
                    embed=self.get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[]
                )

    async def on_shutdown(self) -> None:
        """
        Stop all drivings and save changes to the database when the bot is shut down
        """
        processed_channels = []
        for active_drive in self.active_drives:
            await active_drive.message.edit(
                embed=self.get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[]
            )
            if active_drive.message.id not in processed_channels:
                await active_drive.message.channel.send("All trucks were stopped due to a bot shutdown!")
                processed_channels.append(active_drive.message.id)
            await players.update(
                active_drive.player,
                position=active_drive.player.position,
                miles=active_drive.player.miles,
                truck_miles=active_drive.player.truck_miles,
                gas=active_drive.player.gas,
            )
