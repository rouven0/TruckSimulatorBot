"""
This module contains the Cog for all truck-related commands
"""
from math import log
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_choice, create_option

import api.players as players
import api.trucks as trucks
import api.symbols as symbols


def get_truck_embed(truck: trucks.Truck) -> discord.Embed:
    """
    Returns an embed with details about the given Truck
    """
    truck_embed = discord.Embed(title=truck.name, description=truck.description, colour=discord.Colour.lighter_grey())
    truck_embed.add_field(name="Gas consumption", value=f"{truck.gas_consumption} litres per mile")
    truck_embed.add_field(name="Gas capacity", value=str(truck.gas_capacity) + " l")
    truck_embed.add_field(name="Price", value="$" + str(truck.price))
    truck_embed.add_field(name="Loading capacity", value=f"{truck.loading_capacity} items")
    truck_embed.set_image(url=truck.image_url)
    return truck_embed


def get_truck_choices() -> list:
    choices = []
    for truck in trucks.get_all():
        choices.append(create_choice(name=truck.name, value=truck.truck_id))
    return choices


class Trucks(commands.Cog):
    """
    Check up your truck and its current load
    """

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @cog_ext.cog_subcommand(base="truck")
    async def show(self, ctx, user: discord.User = None) -> None:
        """
        Get details about your truck and the trucks of your friends
        """
        if isinstance(user, str):
            user = await self.bot.fetch_user(int(user))
        if user is not None:
            player = await players.get(user.id)
            avatar_url = user.avatar_url
        else:
            player = await players.get(ctx.author.id)
            avatar_url = ctx.author.avatar_url
        # Detect, when the player is renamed
        if player.name != ctx.author.name:
            await players.update(player, name=ctx.author.name)
        truck = trucks.get(player.truck_id)
        truck_embed = get_truck_embed(truck)
        truck_embed.set_author(name="{}'s truck".format(player.name), icon_url=avatar_url)
        truck_embed.set_footer(
            icon_url=self.bot.user.avatar_url,
            text="See all trucks with `/truck list` and change your truck with `/truck buy`",
        )
        await ctx.send(embed=truck_embed)

    @cog_ext.cog_subcommand(
        base="truck",
        options=[
            create_option(
                name="truck",
                description="The truck you want to buy",
                option_type=4,
                required=True,
                choices=get_truck_choices(),
            )
        ],
    )
    async def buy(self, ctx, truck) -> None:
        """
        Buy a new truck, your old one will be sold and your miles will be reset
        """
        if await players.is_driving(ctx.author.id):
            await ctx.send(f"{ctx.author.mention} You can't buy a new truck while you are driving in the old one")
            return
        player = await players.get(ctx.author.id)
        old_truck = trucks.get(player.truck_id)
        new_truck = trucks.get(truck)
        selling_price = round(old_truck.price - (old_truck.price / 10) * log(player.truck_miles + 1))
        end_price = new_truck.price - selling_price
        # this also adds money if the end price is negative
        await player.debit_money(end_price)
        await players.update(player, truck_miles=0, gas=new_truck.gas_capacity, truck_id=new_truck.truck_id)
        answer_embed = discord.Embed(
            description=f"You sold your old {old_truck.name} for ${selling_price} and bought a brand new {new_truck.name} for ${new_truck.price}",
            colour=discord.Colour.lighter_grey(),
        )
        answer_embed.set_author(name="You got a new truck", icon_url=self.bot.user.avatar_url)
        answer_embed.set_footer(text="Check out your new baby with `/truck show`")
        await ctx.send(embed=answer_embed)

    @cog_ext.cog_subcommand(
        base="truck",
        options=[
            create_option(
                name="truck",
                description="The truck you want to view",
                option_type=4,
                required=True,
                choices=get_truck_choices(),
            )
        ],
    )
    async def view(self, ctx, truck) -> None:
        """
        View details about a specific truck
        """
        truck_embed = get_truck_embed(trucks.get(truck))
        truck_embed.set_footer(
            icon_url=self.bot.user.avatar_url,
            text="See all trucks with `/truck list` and change your truck with `/truck buy`",
        )
        await ctx.send(embed=truck_embed)

    @cog_ext.cog_subcommand(base="truck")
    async def list(self, ctx) -> None:
        """
        Lists all available Trucks
        """
        list_embed = discord.Embed(title="All available trucks", colour=discord.Colour.lighter_grey())
        for truck in trucks.get_all():
            list_embed.add_field(
                name=truck.name, value="Id: {} \n Price: ${:,}".format(truck.truck_id, truck.price), inline=False
            )
        list_embed.set_footer(
            icon_url=self.bot.user.avatar_url, text="Get more information about a truck with `/truck view <id>`"
        )
        await ctx.send(embed=list_embed)

    @cog_ext.cog_slash()
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
        load_embed = discord.Embed(
            title="Your currently loaded items", description=item_list, colour=discord.Colour.lighter_grey()
        )
        load_embed.set_footer(
            text=f"Loaded items: {len(player.loaded_items)}/{trucks.get(player.truck_id).loading_capacity}"
        )
        await ctx.send(embed=load_embed)


def setup(bot):
    bot.add_cog(Trucks(bot))
