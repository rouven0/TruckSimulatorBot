
"""
This module contains the Cog for all truck-related commands
"""
from math import log
import discord
from discord.ext import commands
from discord_slash import cog_ext

import players
import trucks
import symbols


def get_truck_embed(truck: trucks.Truck) -> discord.Embed:
    """
    Returns an embed with details about the given Truck
    """
    truck_embed = discord.Embed(title=truck.name, description=truck.description, colour=discord.Colour.gold())
    truck_embed.add_field(name="Gas consumption", value=f"{truck.gas_consumption} litres per mile")
    truck_embed.add_field(name="Gas capacity", value=str(truck.gas_capacity) + " l")
    truck_embed.add_field(name="Price", value="$" + str(truck.price))
    truck_embed.add_field(name="Loading capacity", value=f"{truck.loading_capacity} items")
    truck_embed.set_image(url=truck.image_url)
    return truck_embed


class Trucks(commands.Cog):
    """
    Check up your truck and its current load
    """

    def __init__(self, bot, driving_commands) -> None:
        self.bot = bot
        self.driving_commands = driving_commands
        super().__init__()

    #@commands.group(pass_context=True, aliases=["t"])
    @cog_ext.cog_subcommand(base="truck", guild_ids=[830928381100556338])
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def mine(self, ctx):
        """
        Get details about your truck
        """
        # if ctx.invoked_subcommand == None:
        player = await players.get(ctx.author.id)
        truck = trucks.get(player.truck_id)

        truck_embed = get_truck_embed(truck)
        truck_embed.set_author(name=f"{ctx.author.name}'s truck", icon_url=ctx.author.avatar_url)
        truck_embed.set_footer(icon_url=self.bot.user.avatar_url,
                                   text="This is your Truck, see all trucks with `t.truck list` and change your truck with `t.truck buy`")

        await ctx.send(embed=truck_embed)

    # @truck.command()
    @cog_ext.cog_subcommand(base="truck", guild_ids=[830928381100556338])
    async def buy(self, ctx, id) -> None:
        """
        Buy a new truck, your old one will be sold and your miles will be reset
        """
        if ctx.author.id in [a.player.user_id for a in self.driving_commands.active_drives]:
            await ctx.send(f"{ctx.author.mention} You can't buy a new truck while you are driving in the old one")
            return
        try:
            id  = int(id)
        except ValueError:
            await ctx.send("Wtf do you want to buy?")
            return
        player = await players.get(ctx.author.id)
        old_truck = trucks.get(player.truck_id)
        new_truck = trucks.get(id)
        selling_price = round(old_truck.price - (old_truck.price / 10) * log(player.truck_miles + 1))
        end_price = new_truck.price - selling_price
        # this also adds money if the end price is negative
        await players.debit_money(player, end_price)
        await players.update(player, truck_miles=0, gas=new_truck.gas_capacity, truck_id=new_truck.truck_id)
        answer_embed = discord.Embed(
            description=f"You sold your old {old_truck.name} for ${selling_price} and bought a brand new {new_truck.name} for ${new_truck.price}",
            colour=discord.Colour.gold())
        answer_embed.set_author(name="You got a new truck", icon_url=self.bot.user.avatar_url)
        answer_embed.set_footer(text="Check out your new baby with `t.truck`")
        await ctx.send(embed=answer_embed)

    # @truck.command()
    @cog_ext.cog_subcommand(base="truck", guild_ids=[830928381100556338])
    async def show(self, ctx, id:int) -> None:
        """
        Shows details about a specific truck
        """
        try:
            id  = int(id)
            truck = trucks.get(id)
            truck_embed = get_truck_embed(truck)
            truck_embed.set_footer(icon_url=self.bot.user.avatar_url,
                                   text="See all trucks with `t.truck list` and change your truck with `t.truck buy`")
            await ctx.send(embed=truck_embed)
        except trucks.TruckNotFound:
            await ctx.send("Truck not found")
        except ValueError:
            await ctx.send("Wtf do you want to show?")

    # @truck.command()
    @cog_ext.cog_subcommand(base="truck", guild_ids=[830928381100556338])
    async def list(self, ctx) -> None:
        """
        Lists all available Trucks
        """
        list_embed = discord.Embed(title="All available trucks", colour=discord.Colour.gold())
        for truck in trucks.get_all():
            list_embed.add_field(name=truck.name,
                                 value="Id: {} \n Price: ${:,}".format(truck.truck_id, truck.price), inline=False)
        list_embed.set_footer(icon_url=self.bot.user.avatar_url,
                              text="Get more information about a truck with `t.truck show <id>`")
        await ctx.send(embed=list_embed)

    # @commands.command()
    @cog_ext.cog_subcommand(base="truck", guild_ids=[830928381100556338])
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def load(self, ctx) -> None:
        """
        Shows what your Truck currently has loaded
        """
        player = await players.get(ctx.author.id)
        item_list = ""
        if len(player.loaded_items) == 0:
            item_list = "Your truck is empty"
        else:
            for item in player.loaded_items:
                item_list += f"{symbols.LIST_ITEM} {self.bot.get_emoji(item.emoji)} {item.name}\n"
        load_embed = discord.Embed(title="Your currently loaded items", description=item_list, colour=discord.Colour.gold())
        load_embed.set_footer(text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}")
        await ctx.send(embed=load_embed)
