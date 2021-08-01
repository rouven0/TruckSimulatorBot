"""
This module contains the Cog for all driving-related commands
"""
from datetime import datetime
from time import time
import discord
from discord.ext import commands
from discord.ext import tasks
from discord_slash import cog_ext
from discord_components import Button, Select, SelectOption
import players
import items
import levels
import places
import symbols
import assets
import jobs
import trucks


class Driving(commands.Cog):
    """
    The heart of the Truck simulator: Drive your Truck on a virtual map
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active_drives = []
        self.gas_price = 0
        super().__init__()

    def get_buttons(self, player: players.Player) -> list:
        """
        Returns buttons based on the players position
        """
        buttons = []
        buttons.append([])
        place = places.get(player.position)
        for symbol in symbols.get_all_drive_symbols():
            if symbol in symbols.get_drive_position_symbols(player.position):
                buttons[0].append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbol)))
            else:
                buttons[0].append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbol), disabled=True))
        buttons[0].append(Button(style=4, label=" ", emoji=self.bot.get_emoji(symbols.STOP)))
        current_job = jobs.get(player.user_id)
        action_buttons = []
        if len(player.loaded_items) < trucks.get(player.truck_id).loading_capacity:
            action_buttons.append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbols.LOAD)))
        if len(player.loaded_items) > 0:
            action_buttons.append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbols.UNLOAD)))
        if player.position == [7, 7]:
            action_buttons.append(Button(style=2, label=" ", emoji=self.bot.get_emoji(symbols.REFILL)))
        if place.name != "Nothing":
            buttons.append(action_buttons)
        if current_job is None:
            buttons.append(Button(style=3, label="New Job", id="new_job"))
        return buttons

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.check_drives.start()

    @commands.Cog.listener()
    async def on_button_click(self, interaction) -> None:
        """
        All the driving reactions are processed here
        Only when the stop sign is he reaction emoji, changes will be applied
        """
        if isinstance(interaction.component, list):
            # Return if buttons are clicked too fast
            await interaction.respond(type=6)
            return
        active_drive = self.get_active_drive(interaction.author.id, message_id=interaction.message.id)
        if active_drive is None:
            await interaction.respond(type=6)
            # Return if the wrong player clicked the button
            return

        try:
            action = int(interaction.component.emoji.id)
        except AttributeError:
            action = interaction.component.id

        if action == "new_job":
            drive_embed = self.get_drive_embed(active_drive.player, interaction.author.avatar_url)
            job = jobs.generate(active_drive.player)
            item = items.get(job.place_from.produced_item)
            job_message =  "{} needs {} {} from {}. You get ${:,} for this transport".format(
                    job.place_to.name, self.bot.get_emoji(item.emoji), item.name, job.place_from.name, job.reward)
            drive_embed.add_field(name="You got a new Job", value=job_message, inline=False)
            await interaction.respond(type=7, embed=drive_embed, components=self.get_buttons(active_drive.player))

        if action == symbols.STOP:
            self.active_drives.remove(active_drive)
            await interaction.message.channel.send("You stopped driving!, {}".format(interaction.author.name))
            await interaction.respond(type=7, components=[])

        if action == symbols.LOAD:
            item = items.get(places.get(active_drive.player.position).produced_item)
            await players.load_item(active_drive.player, item)
            job_message = None

            current_job = jobs.get(interaction.author.id)
            if current_job is not None and item.name == current_job.place_from.produced_item:
                current_job.state = jobs.STATE_LOADED
                job_message = jobs.get_state(current_job)
                jobs.update(current_job, state=current_job.state)

            drive_embed = self.get_drive_embed(active_drive.player, interaction.author.avatar_url)
            drive_embed.add_field(name="Loading successful", value=f"You loaded {self.bot.get_emoji(item.emoji)} {item.name} into your truck", inline=False)
            #This order is required to fit the navigation to the right place
            if job_message is not None:
                drive_embed.add_field(name="Job Notification", value=job_message)
            await interaction.respond(type=7, embed=drive_embed, components=self.get_buttons(active_drive.player))

        if action == symbols.UNLOAD:
            drive_embed = self.get_drive_embed(active_drive.player, interaction.author.avatar_url)
            item_options = []
            for item in active_drive.player.loaded_items:
                # add the item if it doesn't already is in the list
                if item.name not in [o.value for o in item_options]:
                    item_options.append(SelectOption(label=item.name, value=item.name, emoji=self.bot.get_emoji(item.emoji)))
            select = Select(placeholder="Choose which items to unload", options=item_options)
            await interaction.respond(type=7, embed=drive_embed, components=[select])
            selection = await self.bot.wait_for("select_option", check=lambda i: i.author.id == interaction.author.id)
            item = items.get(selection.component[0].label)
            await players.unload_item(active_drive.player, item)

            current_job = jobs.get(interaction.author.id)
            if current_job is not None and item.name == current_job.place_from.produced_item:
                current_job.state = jobs.STATE_DONE
                await players.add_money(active_drive.player, current_job.reward)
                jobs.remove(current_job)
                job_message = jobs.get_state(current_job) + await players.add_xp(active_drive.player, levels.get_job_reward_xp(active_drive.player.level))
                # get the drive embed egain to fit the job update
                drive_embed = self.get_drive_embed(active_drive.player, interaction.author.avatar_url)
                drive_embed.add_field(name="Job Notification", value=job_message)
            drive_embed.add_field(name="Unloading successful", value=f"You removed {self.bot.get_emoji(item.emoji)} {item.name} from your truck", inline=False)

            await selection.respond(type=7, embed=drive_embed, components=self.get_buttons(active_drive.player))

        if action == symbols.REFILL:
            gas_amount = trucks.get(active_drive.player.truck_id).gas_capacity - active_drive.player.gas
            price = round(gas_amount * self.gas_price)

            try:
                await players.debit_money(active_drive.player, price)
            except players.NotEnoughMoney:
                if active_drive.player.gas < 170:
                    await interaction.send(
                        f"{interaction.author.mention} We have a problem: You don't have enough money. Lets make a deal. "
                        "I will give you 100 litres of gas, and you lose 2 levels")
                    if active_drive.player.level > 2:
                        await players.update(active_drive.player, gas=active_drive.player.gas+100, level=active_drive.player.level - 2, xp=0)
                    else:
                        await players.update(active_drive.player, gas=active_drive.player.gas+100, xp=0)
                else:
                    await interaction.send(f"{interaction.author.mention} you don't have enough money to do this. "
                                            "Do some jobs and come back if you have enough")
                drive_embed = self.get_drive_embed(active_drive.player, interaction.author.avatar_url)
                await interaction.respond(type=7, embed=drive_embed, components=self.get_buttons(active_drive.player))
                return

            await players.update(active_drive.player, gas=trucks.get(active_drive.player.truck_id).gas_capacity)
            drive_embed = self.get_drive_embed(active_drive.player, interaction.author.avatar_url)
            drive_embed.add_field(name="Thank you for visiting our gas station",
                                  value=f"You filled {gas_amount} litres into your truck and payed ${price}")
            drive_embed.set_footer(
                text="Wonder how the gas prices are calculated? Check out the daily gas prices in the official server",
                icon_url=self.bot.user.avatar_url)
            await interaction.respond(type=7, embed=drive_embed, components=self.get_buttons(active_drive.player))

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
            active_drive.player.truck_miles += 1
            active_drive.player.gas -= trucks.get(active_drive.player.truck_id).gas_consumption
            if 25 < active_drive.player.gas < 30:
                await active_drive.message.channel.send(f"<@{active_drive.player.user_id}> you are running out of gas. "
                                                        "Please drive to the nearest gas station")

            if active_drive.player.gas <= 0:
                active_drive.player.gas = 1
                await active_drive.message.channel.send(
                    f"<@{active_drive.player.user_id}> You messed up and ran out of gas. "
                    "The company had to have your truck towed away. You will pay $3000 for this incident!")
                try:
                    await players.debit_money(active_drive.player, 3000)
                except players.NotEnoughMoney:
                    await active_drive.message.channel.send(
                        "You are lucky that you don't have enough money. I'll let you go, for now...")
                await players.update(active_drive.player, gas=50, position=[7, 7])
                await interaction.respond(type=7, components=[])
                self.active_drives.remove(active_drive)
                return

            await interaction.message.edit(embed=self.get_drive_embed(active_drive.player, interaction.author.avatar_url),
                                           components=self.get_buttons(active_drive.player))
            await interaction.respond(type=6)

        await players.update(active_drive.player, position=active_drive.player.position,
                                                  miles=active_drive.player.miles,
                                                  truck_miles=active_drive.player.truck_miles,
                                                  gas=active_drive.player.gas)

    @cog_ext.cog_subcommand(base="truck")
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def drive(self, ctx) -> None:
        """
        Start driving your Truck on the map and control it with buttons
        """
        player = await players.get(ctx.author.id)
        # Detect, when the player is renamed
        if player.name != ctx.author.name:
            await players.update(player, name=ctx.author.name)
        if ctx.author.id in [a.player.user_id for a in self.active_drives]:
            active_drive = self.get_active_drive(ctx.author.id)
            await ctx.send(embed=discord.Embed(title=f"Hey {ctx.author.name}",
                                   description="You can't drive on two roads at once!\n"
                                   f"Click [here]({active_drive.message.jump_url}) to jump right back into your Truck",
                                   colour=discord.Colour.gold()))
            return
        await ctx.send("Preparing your Truck...")
        message = await ctx.channel.send(embed=self.get_drive_embed(player, ctx.author.avatar_url),
                                         components=self.get_buttons(player))
        self.active_drives.append(players.ActiveDrive(player, message, time()))

    @cog_ext.cog_subcommand(base="truck")
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def stop(self, ctx) -> None:
        """
        An alternate stop method if there is a problem with the buttons
        """
        active_drive = self.get_active_drive(ctx.author.id)
        if active_drive is None:
            await ctx.send("Nothing to do here")
            return
        self.active_drives.remove(active_drive)
        await active_drive.message.edit(
            embed=self.get_drive_embed(active_drive.player, ctx.author.avatar_url), components=[])
        await ctx.send("You stopped driving!, {}".format(ctx.author.name))
        await players.update(active_drive.player,
                       position=active_drive.player.position,
                       miles=active_drive.player.miles,
                       truck_miles=active_drive.player.truck_miles,
                       gas=active_drive.player.gas)


    @cog_ext.cog_subcommand(base="truck")
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def position(self, ctx) -> None:
        """
        Provides some information about your current position and the things located there
        """
        player = await players.get(ctx.author.id)
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

    # @commands.command(aliases=["places", "ab", "map"])
    @cog_ext.cog_slash()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def addressbook(self, ctx) -> None:
        """
        Lists all public places. Hidden ones are excluded
        """
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.gold())
        for place in places.get_public():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.send(embed=places_embed)

    def get_drive_embed(self, player: players.Player, avatar_url: str) -> discord.Embed:
        """
        Returns the drive embed that includes all the information about the current position and gas
        """
        place = places.get(player.position)
        drive_embed = discord.Embed(description="Enjoy the new images",
                                    colour=discord.Colour.gold(),
                                    timestamp=datetime.utcnow())
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
            drive_embed.add_field(name="Navigation: Drive to {}".format(navigation_place.name),
                                  value=str(navigation_place.position))

        if place.image_url_default is not None:
            drive_embed.add_field(name="What is here?", value=f"{self.bot.get_emoji(items.get(place.produced_item).emoji)} {place.name}", inline=False)
            drive_embed.set_image(url=assets.get_place_image(player, place))
        else:
            drive_embed.set_image(url=assets.get_default(player))
        drive_embed.set_footer(text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}")
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
                item = items.get(map_place.produced_item)
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

    def get_active_drive(self, player_id, message_id=None) -> players.ActiveDrive:
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
                await players.update(active_drive.player, position=active_drive.player.position,
                               miles=active_drive.player.miles,
                               truck_miles=active_drive.player.truck_miles,
                               gas=active_drive.player.gas)
                await active_drive.message.edit(
                    embed=self.get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[])

    async def on_shutdown(self) -> None:
        """
        Stop all drivings and save changes to the database when the bot is shut down
        """
        processed_channels = []
        for active_drive in self.active_drives:
            await active_drive.message.edit(
                embed=self.get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[])
            if active_drive.message.id not in processed_channels:
                await active_drive.message.channel.send("All trucks were stopped due to a bot shutdown!")
                processed_channels.append(active_drive.message.id)
            await players.update(active_drive.player, position=active_drive.player.position,
                           miles=active_drive.player.miles,
                           truck_miles=active_drive.player.truck_miles,
                           gas=active_drive.player.gas)
