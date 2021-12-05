"""
This module contains the Cog for all driving-related commands
"""
import asyncio
from datetime import datetime
import logging
from time import time

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
import config
import api.players as players
import api.companies as companies
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
        super().__init__()

    async def get_buttons(self, player: players.Player) -> list:
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
        current_job = await player.get_job()
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

        if "refill" in place.commands:
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
        player = await players.get_driving_player(ctx.author_id, ctx.origin_message_id)
        await player.stop_drive()
        await ctx.edit_origin(components=[])

    @cog_ext.cog_component()
    async def load(self, ctx: ComponentContext):
        player = await players.get_driving_player(ctx.author_id, ctx.origin_message_id)

        item = items.get(places.get(player.position).produced_item)
        await player.load_item(item)
        job_message = None

        current_job = await player.get_job()
        if current_job is not None and item.name == current_job.place_from.produced_item:
            current_job.state = jobs.STATE_LOADED
            job_message = jobs.get_state(current_job)
            await player.update_job(current_job, state=current_job.state)

        drive_embed = await self.get_drive_embed(player, ctx.author.avatar_url)
        drive_embed.add_field(
            name="Loading successful",
            value=f"You loaded {self.bot.get_emoji(item.emoji)} {item.name} into your truck",
            inline=False,
        )
        # This order is required to fit the navigation to the right place
        await ctx.edit_origin(embed=drive_embed, components=await self.get_buttons(player))
        if job_message is not None:
            await ctx.send(
                embed=discord.Embed(
                    title="Job Notification", description=job_message, colour=discord.Colour.lighter_grey()
                ),
                hidden=True,
            )

    @cog_ext.cog_component()
    async def unload(self, ctx: ComponentContext):
        player = await players.get_driving_player(ctx.author_id, ctx.origin_message_id)

        place = places.get(player.position)
        drive_embed = await self.get_drive_embed(player, ctx.author.avatar_url)
        item_options = []
        for item in player.loaded_items:
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
        item_string = ""
        try:
            selection_ctx: ComponentContext = await wait_for_component(self.bot, components=select, timeout=30)
        except asyncio.exceptions.TimeoutError:
            return
        for name in selection_ctx.selected_options:
            item = items.get(name)
            await player.unload_item(item)
            if name == selection_ctx.selected_options[0]:
                item_string += f"{self.bot.get_emoji(item.emoji)} {item.name}"
            elif name == selection_ctx.selected_options[-1]:
                item_string += f" and {self.bot.get_emoji(item.emoji)} {item.name}"
            else:
                item_string += f", {self.bot.get_emoji(item.emoji)} {item.name}"

        drive_embed = await self.get_drive_embed(player, ctx.author.avatar_url)

        current_job = await player.get_job()
        drive_embed.add_field(
            name="Unloading successful", value=f"You removed {item_string} from your truck", inline=False
        )
        if (
            current_job is not None
            and current_job.place_from.produced_item in selection_ctx.selected_options
            and player.position == current_job.place_to.position
        ):
            current_job.state = jobs.STATE_DONE
            await player.add_money(current_job.reward)
            await player.remove_job(current_job)
            job_message = jobs.get_state(current_job) + await player.add_xp(levels.get_job_reward_xp(player.level))
            if player.company is not None:
                company = await companies.get(player.company)
                await company.add_net_worth(int(current_job.reward / 10))
                job_message += f"\nYour company's net worth was increased by ${int(current_job.reward/10):,}"
            # get the drive embed egain to fit the job update
            drive_embed = await self.get_drive_embed(player, ctx.author.avatar_url)
            await ctx.send(
                embed=discord.Embed(
                    title="Job Notification", description=job_message, colour=discord.Colour.lighter_grey()
                ),
                hidden=True,
            )
        if place.accepted_item in selection_ctx.selected_options:
            await player.add_money(place.item_reward)
            await ctx.send(
                embed=discord.Embed(
                    title="Minijob Notification",
                    description=f"{place.name} gave you ${place.item_reward * (player.level + 1):,} for bringing them {place.accepted_item}",
                    colour=discord.Colour.lighter_grey(),
                ),
                hidden=True,
            )

        drive_embed.add_field(
            name="Unloading successful", value=f"You removed {item_string} from your truck", inline=False
        )
        await selection_ctx.edit_origin(embed=drive_embed, components=await self.get_buttons(player))

    @cog_ext.cog_component()
    async def cancel(self, ctx: ComponentContext):
        player = await players.get_driving_player(ctx.author_id, ctx.origin_message_id)
        await ctx.edit_origin(
            embed=await self.get_drive_embed(player, ctx.author.avatar_url),
            components=await self.get_buttons(player),
        )

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext) -> None:
        """
        This method is only used to process the directional_buttons for the driving
        """
        try:
            direction = int(ctx.custom_id)
        except ValueError:
            return
        if direction not in symbols.get_all_drive_symbols():
            return

        try:
            player = await players.get_driving_player(ctx.author_id, ctx.origin_message_id)
        except players.NotDriving:
            await ctx.defer(ignore=True)
            return

        if direction == symbols.LEFT:
            player.position = [player.position[0] - 1, player.position[1]]

        if direction == symbols.UP:
            player.position = [player.position[0], player.position[1] + 1]

        if direction == symbols.DOWN:
            player.position = [player.position[0], player.position[1] - 1]

        if direction == symbols.RIGHT:
            player.position = [player.position[0] + 1, player.position[1]]

        await player.set_last_action_time(int(time()))
        player.miles += 1
        player.truck_miles += 1
        player.gas -= trucks.get(player.truck_id).gas_consumption

        if player.gas <= 0:
            await ctx.edit_origin(components=[])
            await ctx.send(
                "You messed up and ran out of gas. "
                "Your company had to have your truck towed away. You will pay $3000 for this incident!"
            )
            try:
                await player.debit_money(3000)
            except players.NotEnoughMoney:
                await ctx.send("You are lucky that you don't have enough money. I'll let you go, for now...")
            await players.update(player, gas=trucks.get(player.truck_id).gas_capacity, position=[7, 7])
            await player.stop_drive()
            return

        await players.update(
            player,
            position=player.position,
            miles=player.miles,
            truck_miles=player.truck_miles,
            gas=player.gas,
        )

        await ctx.edit_origin(
            embed=await self.get_drive_embed(player, ctx.author.avatar_url),
            components=await self.get_buttons(player),
        )
        if 60 < player.gas < 70:
            await ctx.send("You are running out of gas. Please drive to the nearest gas station", hidden=True)

    @cog_ext.cog_slash()
    async def drive(self, ctx) -> None:
        """
        Start driving your Truck on the map and control it with buttons
        """
        player = await players.get(ctx.author.id)

        if await players.is_driving(ctx.author.id):
            await (await players.get_driving_player(ctx.author.id)).stop_drive()

        player = players.DrivingPlayer(*tuple(await players.get(ctx.author.id)))
        message = await ctx.send(
            embed=await self.get_drive_embed(player, ctx.author.avatar_url),
            components=await self.get_buttons(player),
        )
        player.message_id = message.id
        player.last_action_time = int(time())
        # Detect, when the player is renamed
        if player.name != ctx.author.name:
            await players.update(player, name=ctx.author.name)
        await player.start_drive()

    @cog_ext.cog_slash()
    async def position(self, ctx) -> None:
        """
        Provides some information about your current position and the things located there
        """
        player = await players.get(ctx.author.id)
        place = places.get(player.position)
        position_embed = discord.Embed(
            description="You are at {}".format(player.position), colour=discord.Colour.lighter_grey()
        )
        position_embed.set_author(name="{}'s Position".format(ctx.author.name), icon_url=ctx.author.avatar_url)
        position_embed.add_field(name="What is here?", value=symbols.LIST_ITEM + place.name, inline=False)
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
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.lighter_grey())
        for place in places.get_public():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.send(embed=places_embed)

    async def get_drive_embed(self, player: players.Player, avatar_url: Asset) -> discord.Embed:
        """
        Returns the drive embed that includes all the information about the current position and gas
        """
        place = places.get(player.position)
        all_companies = await companies.get_all()
        drive_embed = discord.Embed(
            description="Now with slash commands!", colour=discord.Colour.lighter_grey(), timestamp=datetime.utcnow()
        )
        drive_embed.set_author(name="{} is driving".format(player.name), icon_url=avatar_url)

        drive_embed.add_field(name="Minimap", value=await self.generate_minimap(player, all_companies), inline=False)
        drive_embed.add_field(name="Position", value=str(player.position))
        drive_embed.add_field(name="Gas left", value=f"{player.gas} l")

        current_job = await player.get_job()
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
        if player.position in [c.hq_position for c in all_companies]:
            for company in all_companies:
                if company.hq_position == player.position:
                    drive_embed.add_field(
                        name="What is here?",
                        value=f"A company called **{company.name}**",
                        inline=False,
                    )
        drive_embed.set_footer(
            text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}"
        )
        return drive_embed

    async def generate_minimap(self, player: players.Player, all_companies: list[companies.Company]) -> str:
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
                # show other trucks on the map
                try:
                    item = items.get(map_place.produced_item)
                except items.ItemNotFound:
                    item = None
                if item is not None:
                    minimap_array[i][j] = str(self.bot.get_emoji(items.get(map_place.produced_item).emoji))
                elif position in [c.hq_position for c in all_companies]:
                    for company in all_companies:
                        if company.hq_position == position:
                            minimap_array[i][j] = company.logo
                elif position[0] in [-1, config.MAP_BORDER + 1] or position[1] in [-1, config.MAP_BORDER + 1]:
                    # Mark the map border with symbols
                    minimap_array[i][j] = ":small_orange_diamond:"
                    if (
                        # Small correction mechanism to prevents the lines from going beyond the border
                        position[0] < -1
                        or position[0] > config.MAP_BORDER + 1
                        or position[1] < -1
                        or position[1] > config.MAP_BORDER + 1
                    ):
                        minimap_array[i][j] = symbols.MAP_BACKGROUND
                else:
                    minimap_array[i][j] = symbols.MAP_BACKGROUND
                    for p in await players.get_all_driving_players():
                        if p.position == position:
                            minimap_array[i][j] = trucks.get(p.truck_id).emoji

        minimap_array[3][3] = trucks.get(player.truck_id).emoji
        minimap = ""
        for i in range(0, 7):
            for j in range(0, 7):
                minimap = minimap + minimap_array[i][j]
            minimap = minimap + "\n"
        return minimap

    @tasks.loop(seconds=20)
    async def check_drives(self) -> None:
        """
        Drives that are inactive for more than 1 hour get stopped
        """
        for player in await players.get_all_driving_players():
            if time() - player.last_action_time > 3600:
                logging.info("Driving of %s timed out", player.name)
                await player.stop_drive()


def setup(bot):
    bot.add_cog(Driving(bot))
