"""
This module contains the Cog for all economy-related commands
"""
from datetime import datetime
from random import randint
import sys

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import players
import places
import jobs


class Economy(commands.Cog):
    """
    Earn money, trade it and buy better Trucks
    """
    def __init__(self, bot: commands.Bot, news_channel_id: int, driving_commands) -> None:
        self.bot = bot
        self.news_channel_id = news_channel_id
        self.scheduler = AsyncIOScheduler()
        self.gas_price = 1
        self.driving_commands = driving_commands
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.news_channel: discord.TextChannel = self.bot.get_channel(self.news_channel_id)

        self.scheduler.add_job(self.daily_gas_prices, trigger="cron", day_of_week="mon-sun", hour=2)

        self.scheduler.start()

        if "--set-gas-price" in sys.argv:
            await self.daily_gas_prices()

    async def daily_gas_prices(self) -> None:
        self.gas_price = randint(50, 200)/100
        gas_embed = discord.Embed(title="Daily Gas Prices", description="Gas prices for {}".format(datetime.utcnow().strftime("%A, %B %d %Y")), colour=discord.Colour.gold())
        gas_embed.add_field(name="Main gas station", value=f"${self.gas_price} per litre")
        try:
            await self.news_channel.send(embed=gas_embed)
        except AttributeError:
            pass

    @commands.command()
    async def job(self, ctx, *args) -> None:
        """
        Get yourself some jobs and earn money
        """
        player = players.get(ctx.author.id)
        current_job = jobs.get(ctx.author.id)
        job_embed = discord.Embed(colour=discord.Colour.gold())
        job_embed.set_author(name="{}'s Job".format(ctx.author.name),
                             icon_url=ctx.author.avatar_url)
        if current_job is None:
            if args and args[0] == "new":
                job_tuple = jobs.generate(player)
                job_embed.add_field(name="You got a new Job", value=job_tuple[1], inline=False)
                job_embed.add_field(name="Current state", value=jobs.get_state(job_tuple[0]))
            else:
                job_embed.add_field(name="You don't have a job at the moment",
                                    value="Type `t.job new` to get one")
        else:
            job_embed.add_field(name="Your current job", value=jobs.show(current_job), inline=False)
            job_embed.add_field(name="Current state", value=jobs.get_state(current_job))
        await ctx.channel.send(embed=job_embed)

    @commands.command()
    async def load(self, ctx) -> None:
        """
        If you have a job, you can load your Truck with items you have to transport
        """
        player = players.get(ctx.author.id)
        current_job = jobs.get(ctx.author.id)
        if current_job is None:
            await ctx.channel.send("Nothing to do here")
            return
        if player.position == current_job.place_from.position:
            current_job.state = 1
            await ctx.channel.send(jobs.get_state(current_job))
            jobs.update(current_job, state=current_job.state)
        else:
            await ctx.channel.send("Nothing to do here")

    @commands.command()
    async def unload(self, ctx) -> None:
        """
        Unload your Truck at the right place to get your job done
        """
        player = players.get(ctx.author.id)
        current_job = jobs.get(ctx.author.id)
        if current_job is None:
            await ctx.channel.send("Nothing to do here")
            return
        if player.position == current_job.place_to.position and current_job.state == 1:
            current_job.state = 2
            await ctx.channel.send(jobs.get_state(current_job)+players.add_xp(player, randint(1, (player.level**2)+7)))
            jobs.remove(current_job)
            players.add_money(player, current_job.reward)
        else:
            await ctx.channel.send("Nothing to do here")

    @commands.command()
    async def refill(self, ctx):
        player = players.get(ctx.author.id)

        if ctx.author.id in [a.player.user_id for a in self.driving_commands.active_drives]:
            active_drive = self.driving_commands.get_active_drive(ctx.author.id)
            await ctx.channel.send(embed=discord.Embed(title=f"Hey {ctx.author.name}",
                                   description="You can't refill a driving vehicle\n"
                                   "Click [here]({}) to jump right back into your Truck".format(active_drive.message.jump_url),
                                   colour=discord.Colour.gold()))
            return
        if "refill" not in places.get(player.position).commands:
            raise places.WrongPlaceError("Do you see a gas pump here?")
        # TODO replace the 600 with the trucks gas max
        gas_amount = 600 - player.gas
        price = round(gas_amount * self.gas_price)

        try:
            players.debit_money(player, price)
        except players.NotEnoughMoney:
            await ctx.channel.send("Guess we have a problem: You don't have enough money. Lets make a deal, I will give you 100 litres of gas, and you lose 2 levels")
            if player.level > 2:
                players.update(player, gas=100, level=player.level-2, xp=0)
            else:
                players.update(player, gas=100, xp=0)
            return

        refill_embed = discord.Embed(title="Thank you for visiting our gas station",
                                    description=f"You filled {gas_amount} litres into your truck and payed ${price}",
                                    colour=discord.Colour.gold())
        refill_embed.set_footer(text="Wonder how these prices are calculated? Check out the daily gas prices in the official server")
        players.update(player, gas=600)
        await ctx.channel.send(embed=refill_embed)

    @commands.command()
    async def give(self, ctx, user: discord.User=None, amount=None) -> None:
        if user is None:
            await ctx.channel.send("No user specified")
            return
        if amount is None:
            await ctx.channel.send("No amount specified")
        try:
            amount = abs(int(amount))
        except ValueError:
            await ctx.channel.send("Wtf")
        donator = players.get(ctx.author.id)
        acceptor = players.get(user.id)
        players.debit_money(donator, amount)
        players.add_money(acceptor, amount)
        give_embed = discord.Embed(description=f"{donator.name} gave ${amount} to {acceptor.name}",
                                   colour=discord.Colour.gold())
        await ctx.channel.send(embed=give_embed)
