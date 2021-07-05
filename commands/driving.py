"""
This module contains the Cog for all driving-related commands
"""
from math import log
from time import time
from random import randint
import asyncio
import discord
from discord.ext import commands
from discord_components import Button
from discord_components.component import Select, SelectOption
import players
import items
import places
import symbols
import assets
import jobs
import trucks


def generate_minimap(player: players.Player) -> str:
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

    minimap_array[3][3] = trucks.get(player.truck_id).emoji
    minimap = ""
    for i in range(0,7):
        for j in range(0, 7):
            minimap = minimap + minimap_array[i][j]
        minimap = minimap + "\n"
    return minimap


def get_drive_embed(player: players.Player, avatar_url: str) -> discord.Embed:
    """
    """
    place = places.get(player.position)
    drive_embed = discord.Embed(description="Keep an eye on your gas!",
                                colour=discord.Colour.gold())
    drive_embed.set_author(name="{} is driving".format(player.name), icon_url=avatar_url)
    drive_embed.add_field(name="Minimap", value=generate_minimap(player), inline=False)
    drive_embed.add_field(name="Position", value=player.position)
    drive_embed.add_field(name="Gas left", value=f"{player.gas} l")
    current_job = jobs.get(player.user_id)
    if current_job is not None:
        if current_job.state == 0:
            navigation_place = current_job.place_from
        else:
            navigation_place = current_job.place_to
        drive_embed.add_field(name="Navigation: Drive to {}".format(navigation_place.name),
                              value=navigation_place.position)
    if place.image_url is not None:
        drive_embed.set_image(url=assets.get_place_image(player, place))
    else:
        drive_embed.set_image(url=assets.get_default(player))
    drive_embed.set_footer(text="Note: Your position is only applied if you stop driving")
    return drive_embed

class Driving(commands.Cog):
    """
    The heart of the Truck simulator: Drive your Truck on a virtual map
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_drives = []

    def get_buttons(self, player: players.Player) -> list:
        """
        Returns buttons based on the players position
        """
        buttons = [[]]
        for symbol in symbols.get_drive_position_symbols(player.position):
            buttons[0].append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbol)))
        buttons[0].append(Button(style=4, label=" ", emoji=self.bot.get_emoji(symbols.STOP)))
        current_job = jobs.get(player.user_id)
        if current_job is not None and player.position == current_job.place_from.position and current_job.state == 0:
            buttons.append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbols.LOAD)))
        if current_job is not None and player.position == current_job.place_to.position and current_job.state == 1:
            buttons.append(Button(style=1, label=" ", emoji=self.bot.get_emoji(symbols.UNLOAD)))
        return buttons

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
            action = interaction.component.label

        if action == symbols.STOP:
            self.active_drives.remove(active_drive)
            await interaction.message.channel.send("You stopped driving!, {}".format(interaction.author.name))
            await interaction.respond(type=7, components=[])
            players.update(active_drive.player, position=active_drive.player.position,
                           miles=active_drive.player.miles, gas=active_drive.player.gas)

        if action == symbols.LOAD:
            current_job = jobs.get(interaction.author.id)
            current_job.state = 1
            await interaction.channel.send(jobs.get_state(current_job))
            jobs.update(current_job, state=current_job.state)
            await interaction.respond(type=7, components=self.get_buttons(active_drive.player))

        if action == symbols.UNLOAD:
            current_job = jobs.get(interaction.author.id)
            current_job.state = 2
            await interaction.channel.send(jobs.get_state(current_job)+
                                           players.add_xp(active_drive.player, randint(1, (active_drive.player.level**2)+7))+
                                           "\nYour position got applied")
            players.add_money(active_drive.player, current_job.reward)
            jobs.remove(current_job)
            players.update(active_drive.player, position=active_drive.player.position,
                           miles=active_drive.player.miles, gas=active_drive.player.gas)
            await interaction.respond(type=7, components=self.get_buttons(active_drive.player))

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
            active_drive.player.gas -= trucks.get(active_drive.player.truck_id).gas_consumption
            if 25 < active_drive.player.gas < 30:
                await active_drive.message.channel.send(f"<@{active_drive.player.user_id}> you are running out of gas. "
                                                        "Please drive to the nearest gas station")

            if active_drive.player.gas <= 0:
                active_drive.player.gas = 1
                players.update(active_drive.player, position=active_drive.player.position,
                               miles=active_drive.player.miles, gas=active_drive.player.gas)
                await active_drive.message.channel.send(f"<@{active_drive.player.user_id}> You messed up and ran out of gas. "
                                                        "The company had to have your truck towed away. You will pay $3000 for this incident!")
                try:
                    players.debit_money(active_drive.player, 3000)
                except players.NotEnoughMoney:
                    await active_drive.message.channel.send("You are lucky that you don't have enough money. I'll let you go, for now...")
                await interaction.respond(type=7, components=[])
                self.active_drives.remove(active_drive)
                return


            await interaction.message.edit(embed=get_drive_embed(active_drive.player,
                                           interaction.author.avatar_url),
                                           components=self.get_buttons(active_drive.player))
            await interaction.respond(type=6)

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def drive(self, ctx) -> None:
        """
        Start driving your Truck on the map and control it with buttons
        """
        player = players.get(ctx.author.id)
        # Detect, when the player is renamed
        if player.name != ctx.author.name:
            players.update(player, name=ctx.author.name)
        if ctx.author.id in [a.player.user_id for a in self.active_drives]:
            active_drive = self.get_active_drive(ctx.author.id)
            await ctx.channel.send(embed=discord.Embed(title=f"Hey {ctx.author.name}",
                                   description="You can't drive on two roads at once!\n"
                                   "Click [here]({}) to jump right back into your Truck".format(active_drive.message.jump_url),
                                   colour=discord.Colour.gold()))
            return
        message = await ctx.channel.send(embed=get_drive_embed(player, ctx.author.avatar_url),
                                         components=self.get_buttons(player))
        self.active_drives.append(players.ActiveDrive(player, message, time()))

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True, add_reactions=True)
    async def stop(self, ctx) -> None:
        """
        This is an alternate stop method to get your changes applied if there is a problem with the reactions
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
                       miles=active_drive.player.miles,
                       gas=active_drive.player.gas)

    @commands.command(aliases=["t", "trucks"])
    async def truck(self, ctx, *args):
        player = players.get(ctx.author.id)

        if args and args[0] == "buy":
            options = []
            for truck in trucks.get_all():
                options.append(SelectOption(label=truck.name, description=truck.description, value=truck.truck_id))

            buy_instrucions = discord.Embed(title="Time for a new Truck?", colour=discord.Colour.gold(),
                                            description="Choose one of the Trucks in the list. \n"
                                            "Your old Truck will be sold and your miles and gas will be reset. \n")
            message = await ctx.channel.send(embed=buy_instrucions, components=[
                Select(placeholder="Select your Truck",
                       options=options) ])

            def check(select_option):
                return select_option.author.id == ctx.author.id

            try:
                selection = await self.bot.wait_for("select_option", check=check, timeout=6)
            except:
                await message.edit("Truck selection timed out", components=[])
                return
            await selection.respond(type=7, components=[])
            selected_truck_id = int(selection.component[0].value)

            old_truck = trucks.get(player.truck_id)
            new_truck = trucks.get(selected_truck_id)
            selling_price = round(old_truck.price-(old_truck.price/10)*log(player.miles+1))
            end_price = new_truck.price - selling_price
            # this also adds money if the end price is negative
            players.debit_money(player, end_price)
            players.update(player, miles=0, gas=new_truck.gas_capacity, truck_id=new_truck.truck_id)
            answer_embed=discord.Embed(description=f"You sold your old {old_truck.name} for ${selling_price} and bought a brand new {new_truck.name} for ${new_truck.price}", 
                                       colour=discord.Colour.gold())
            answer_embed.set_author(name="You got a new truck", icon_url=self.bot.user.avatar_url)
            answer_embed.set_footer(text="Check out your new baby with `t.truck`")
            await ctx.channel.send(embed=answer_embed)

            return

        if args and args[0] == "list":
            list_embed = discord.Embed(title="All available trucks", colour=discord.Colour.gold())
            for truck in trucks.get_all():
                list_embed.add_field(name=truck.name, value="Id: {} \n Price: ${:,}".format(truck.truck_id, truck.price), inline=False)
            list_embed.set_footer(icon_url=self.bot.user.avatar_url, text="Get more information about a truck with `t.truck show <id>`")
            await ctx.channel.send(embed=list_embed)
            return

        if args and args[0] == "show":
            try:
                truck = trucks.get(int(args[1]))
                is_own_truck=False
            except trucks.TruckNotFound:
                await ctx.channel.send("Truck not found")
                return
            except (ValueError, IndexError):
                await ctx.channel.send("**Syntax** `t.truck show <id>`")
                return
        else:
            truck = trucks.get(player.truck_id)
            is_own_truck=True


        truck_embed = self.get_truck_embed(truck)
        if is_own_truck:
            truck_embed.set_author(name=f"{ctx.author.name}'s truck", icon_url=ctx.author.avatar_url)
            truck_embed.set_footer(icon_url=self.bot.user.avatar_url, text="This is your Truck, see all trucks with `t.truck list` and change your truck with `t.truck buy`")
        else:
            truck_embed.set_footer(icon_url=self.bot.user.avatar_url, text="See all trucks with `t.truck list` and change your truck with `t.truck buy`")

        await ctx.channel.send(embed=truck_embed)

    def get_truck_embed(self, truck: trucks.Truck) -> discord.Embed:
        truck_embed = discord.Embed(title=truck.name, description=truck.description, colour=discord.Colour.gold())
        truck_embed.add_field(name="Gas consumption", value=f"{truck.gas_consumption} litres per mile")
        truck_embed.add_field(name="Gas capacity", value = str(truck.gas_capacity)+" l")
        truck_embed.add_field(name="Price", value = "$"+str(truck.price))
        truck_embed.set_image(url=truck.image_url)
        return truck_embed

    @commands.command(aliases=["here"])
    async def position(self, ctx) -> None:
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
    def get_place_commands(command_list) -> str:
        """
        Returns a string in which all available commands for this place are listed
        """
        readable = ""
        for command in command_list:
            readable = "{}{}`{}`\n".format(readable, symbols.LIST_ITEM, command)
        return readable

    @commands.command(aliases=["places", "ab"])
    async def addressbook(self, ctx) -> None:
        """
        Lists all public places. Hidden ones are excluded
        """
        places_embed = discord.Embed(title="All public known Places", colour=discord.Colour.gold())
        for place in places.get_public():
            places_embed.add_field(name=place.name, value=place.position)
        await ctx.channel.send(embed=places_embed)

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

    async def check_drives(self) -> None:
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
                                   miles=active_drive.player.miles,
                                   gas=active_drive.player.gas)
            await asyncio.sleep(10)

    async def on_shutdown(self) -> None:
        """
        Stop all drivings and save changes to the database when the bot is shut down
        """
        processed_channels = []
        for active_drive in self.active_drives:
            await active_drive.message.edit(
                embed=get_drive_embed(active_drive.player, self.bot.user.avatar_url), components=[])
            if active_drive.message.channel.id not in processed_channels:
                await active_drive.message.channel.send("All trucks were stopped due to a bot shutdown!")
                processed_channels.append(active_drive.message.channel.id)
            players.update(active_drive.player, position=active_drive.player.position, miles=active_drive.player.miles, gas=active_drive.player.gas)
