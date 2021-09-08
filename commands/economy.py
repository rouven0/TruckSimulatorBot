"""
This module contains the Cog for all economy-related commands
"""
from datetime import datetime
import logging
from random import randint
from typing import Optional
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_commands import create_option
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import players
import places
import items
import jobs
import trucks


class Economy(commands.Cog):
    """
    Earn money, trade it and buy better Trucks
    """

    def __init__(self, bot: commands.Bot, news_channel_id: int, driving_commands) -> None:
        self.bot = bot
        self.news_channel_id = news_channel_id
        self.news_channel: Optional[discord.TextChannel] = None
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.daily_gas_prices, trigger="cron", day_of_week="mon-sun", hour=2)
        self.driving_commands = driving_commands
        gas_file = open("gas.txt", "r")
        self.gas_price = float(gas_file.readline())
        self.driving_commands.gas_price = self.gas_price
        logging.info(f"Starting with gas price {self.gas_price}")
        gas_file.close()
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.news_channel = self.bot.get_channel(self.news_channel_id)
        self.scheduler.start()

    async def daily_gas_prices(self) -> None:
        """
        Set the daily gas price and show it in the support server
        """
        self.gas_price = randint(50, 200) / 100
        gas_embed = discord.Embed(
            title="Daily Gas Prices",
            description="Gas prices for {}".format(datetime.utcnow().strftime("%A, %B %d %Y")),
            colour=discord.Colour.gold(),
        )
        gas_embed.add_field(name="Main gas station", value=f"${self.gas_price} per litre")
        if self.news_channel is None:
            return
        await self.news_channel.send(embed=gas_embed)
        self.driving_commands.gas_price = self.gas_price
        logging.info(f"The new gas price is {self.gas_price}")
        gas_file = open("gas.txt", "w")
        gas_file.write(str(self.gas_price))
        gas_file.close()

    @cog_ext.cog_component()
    async def show_job(self, ctx: ComponentContext) -> None:
        """
        Shows your current job
        """
        current_job = jobs.get(ctx.author.id)
        if current_job is None:
            # return when there are errors with the job
            return
        job_embed = discord.Embed(colour=discord.Colour.gold())
        job_embed.set_author(name="{}'s Job".format(ctx.author.name), icon_url=ctx.author.avatar_url)
        place_from = current_job.place_from
        place_to = current_job.place_to
        item = items.get(place_from.produced_item)
        job_message = "Bring {} {} from {} to {}.".format(
            self.bot.get_emoji(item.emoji), item.name, place_from.name, place_to.name
        )
        job_embed.add_field(name="Your current job", value=job_message, inline=False)
        job_embed.add_field(name="Current state", value=jobs.get_state(current_job))
        await ctx.send(embed=job_embed, hidden=True)

    @cog_ext.cog_component()
    async def new_job(self, ctx: ComponentContext) -> None:
        """
        Get a new job
        """
        active_drive = self.driving_commands.get_active_drive(ctx.author_id, ctx.origin_message_id)
        job_embed = discord.Embed(colour=discord.Colour.gold())
        job_embed.set_author(name="{}'s Job".format(ctx.author.name), icon_url=ctx.author.avatar_url)
        job = jobs.generate(active_drive.player)
        item = items.get(job.place_from.produced_item)
        job_message = "{} needs {} {} from {}. You get ${:,} for this transport".format(
            job.place_to.name, self.bot.get_emoji(item.emoji), item.name, job.place_from.name, job.reward
        )
        job_embed.add_field(name="You got a new Job", value=job_message, inline=False)
        job_embed.add_field(name="Current state", value=jobs.get_state(job))
        await ctx.edit_origin(
            embed=self.driving_commands.get_drive_embed(active_drive.player, ctx.author.avatar_url),
            components=self.driving_commands.get_buttons(active_drive.player),
        )
        await ctx.send(embed=job_embed, hidden=True)

    @cog_ext.cog_component()
    async def refill(self, ctx: ComponentContext):
        """
        If you're at the gas station, you can refill your truck's gas
        """
        active_drive = self.driving_commands.get_active_drive(ctx.author_id, ctx.origin_message_id)
        gas_amount = trucks.get(active_drive.player.truck_id).gas_capacity - active_drive.player.gas
        price = round(gas_amount * self.gas_price)

        try:
            await players.debit_money(active_drive.player, price)
        except players.NotEnoughMoney:
            if active_drive.player.gas < 170:
                await ctx.send(
                    f"{ctx.author.mention} We have a problem: You don't have enough money. Lets make a deal. "
                    "I will give you 100 litres of gas, and you lose 2 levels",
                    hidden=True,
                )
                if active_drive.player.level > 2:
                    await players.update(
                        active_drive.player,
                        gas=active_drive.player.gas + 100,
                        level=active_drive.player.level - 2,
                        xp=0,
                    )
                else:
                    await players.update(active_drive.player, gas=active_drive.player.gas + 100, xp=0)
            else:
                await ctx.send(
                    f"{ctx.author.mention} you don't have enough money to do this. "
                    "Do some jobs and come back if you have enough",
                    hidden=True,
                )
            return

        refill_embed = discord.Embed(
            title="Thank you for visiting our gas station",
            description=f"You filled {gas_amount} litres into your truck and payed ${price}",
            colour=discord.Colour.gold(),
        )
        refill_embed.set_footer(
            text="Wonder how these prices are calculated? Check out the daily gas prices in the official server"
        )
        await players.update(active_drive.player, gas=trucks.get(active_drive.player.truck_id).gas_capacity)
        await ctx.edit_origin(embed=self.driving_commands.get_drive_embed(active_drive.player, ctx.author.avatar_url))
        await ctx.send(embed=refill_embed, hidden=True)

    @cog_ext.cog_slash()
    async def give(self, ctx, user: discord.User, amount: int) -> None:
        """
        Do I really have to explain this?
        """
        amount = abs(int(amount))
        donator = await players.get(ctx.author.id)
        acceptor = await players.get(user.id)
        await players.debit_money(donator, amount)
        await players.add_money(acceptor, amount)
        give_embed = discord.Embed(
            description=f"{donator.name} gave ${amount} to {acceptor.name}", colour=discord.Colour.gold()
        )
        await ctx.send(embed=give_embed)

    @cog_ext.cog_slash(
        options=[
            create_option(
                name="item",
                description="The item you want to view",
                option_type=3,
                choices=[i.name for i in items.get_all()],
                required=True,
            )
        ]
    )
    async def iteminfo(self, ctx, item: str) -> None:
        requested_item = items.get(item)
        item_embed = discord.Embed(
            title=f"Item info for {requested_item.name}",
            description=requested_item.description,
            colour=discord.Colour.gold(),
        )
        for place in places.get_all():
            if place.produced_item == item:
                item_embed.add_field(name="Found at", value=place.name)
        await ctx.send(embed=item_embed)
