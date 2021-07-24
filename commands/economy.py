"""
This module contains the Cog for all economy-related commands
"""
from datetime import datetime
import logging
from random import randint
import discord
from discord.ext import commands
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
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.daily_gas_prices, trigger="cron", day_of_week="mon-sun", hour=2)
        self.driving_commands = driving_commands
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.news_channel: discord.TextChannel = self.bot.get_channel(self.news_channel_id)
        self.scheduler.start()
        gas_file = open("gas.txt", "r")
        self.gas_price = float(gas_file.readline())
        self.driving_commands.gas_price = self.gas_price
        logging.info(f"Starting with gas price {self.gas_price}")
        gas_file.close()

    async def daily_gas_prices(self) -> None:
        """
        Set the daily gas price and show it in the support server
        """
        self.gas_price = randint(50, 200) / 100
        gas_embed = discord.Embed(title="Daily Gas Prices",
                                  description="Gas prices for {}".format(datetime.utcnow().strftime("%A, %B %d %Y")),
                                  colour=discord.Colour.gold())
        gas_embed.add_field(name="Main gas station", value=f"${self.gas_price} per litre")
        try:
            await self.news_channel.send(embed=gas_embed)
            self.driving_commands.gas_price = self.gas_price
            logging.info(f"The new gas price is {self.gas_price}")
            gas_file = open("gas.txt", "w")
            gas_file.write(str(self.gas_price))
            gas_file.close()
        except AttributeError:
            pass

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def job(self, ctx, *args) -> None:
        """
        Get yourself some jobs and earn money
        """
        player = await players.get(ctx.author.id)
        current_job = jobs.get(ctx.author.id)
        job_embed = discord.Embed(colour=discord.Colour.gold())
        job_embed.set_author(name="{}'s Job".format(ctx.author.name),
                             icon_url=ctx.author.avatar_url)
        if current_job is None:
            if args and args[0] == "new":
                job = jobs.generate(player)
                item = items.get(job.place_from.produced_item)
                job_message =  "{} needs {} {} from {}. You get ${:,} for this transport".format(
                        job.place_to.name, self.bot.get_emoji(item.emoji), item.name, job.place_from.name, job.reward)
                job_embed.add_field(name="You got a new Job", value=job_message, inline=False)
                job_embed.add_field(name="Current state", value=jobs.get_state(job))
                if ctx.author.id in [a.player.user_id for a in self.driving_commands.active_drives]:
                    active_drive = self.driving_commands.get_active_drive(ctx.author.id)
                    await active_drive.message.edit(embed=self.driving_commands.get_drive_embed(active_drive.player, ctx.author.avatar_url),
                                                    components=self.driving_commands.get_buttons(active_drive.player))
            else:
                job_embed.add_field(name="You don't have a job at the moment",
                                    value="Type `t.job new` to get one")
        else:
            place_from = current_job.place_from
            place_to = current_job.place_to
            item = items.get(place_from.produced_item)
            job_message= "Bring {} {} from {} to {}.".format(self.bot.get_emoji(item.emoji), item.name, place_from.name, place_to.name)
            job_embed.add_field(name="Your current job", value=job_message, inline=False)
            job_embed.add_field(name="Current state", value=jobs.get_state(current_job))
        await ctx.channel.send(embed=job_embed)


    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def refill(self, ctx):
        """
        If you're at the gas station, you can refill your truck's gas
        """
        player = await players.get(ctx.author.id)

        if ctx.author.id in [a.player.user_id for a in self.driving_commands.active_drives]:
            active_drive = self.driving_commands.get_active_drive(ctx.author.id)
            await ctx.channel.send(
                    embed=discord.Embed(title=f"Hey {ctx.author.name}",
                                       description="You can't refill a driving vehicle\n"
                                                   "Click [here]({}) to jump right back into your Truck".format(active_drive.message.jump_url),
                                       colour=discord.Colour.gold()))
            return

        if "refill" not in places.get(player.position).commands:
            raise places.WrongPlaceError("Do you see a gas pump here?")

        gas_amount = trucks.get(player.truck_id).gas_capacity - player.gas
        price = round(gas_amount * self.gas_price)

        try:
            await players.debit_money(player, price)
        except players.NotEnoughMoney:
            if player.gas < 170:
                await ctx.channel.send(
                    f"{ctx.author.mention} We have a problem: You don't have enough money. Lets make a deal. "
                "I will give you 100 litres of gas, and you lose 2 levels")
                if player.level > 2:
                    await players.update(player, gas=player.gas+100, level=player.level - 2, xp=0)
                else:
                    await players.update(player, gas=player.gas+100, xp=0)
            else:
                await ctx.channel.send(f"{ctx.author.mention} you don't have enough money to do this. "
                                            "Do some jobs and come back if you have enough")
            return

        refill_embed = discord.Embed(title="Thank you for visiting our gas station",
                                     description=f"You filled {gas_amount} litres into your truck and payed ${price}",
                                     colour=discord.Colour.gold())
        refill_embed.set_footer(
            text="Wonder how these prices are calculated? Check out the daily gas prices in the official server")
        await players.update(player, gas=trucks.get(player.truck_id).gas_capacity)
        await ctx.channel.send(embed=refill_embed)

    @commands.command()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def give(self, ctx, user: discord.User = None, amount=None) -> None:
        """
        Do I really have to explain this?
        """
        if user is None:
            await ctx.channel.send("No user specified")
            return
        if amount is None:
            await ctx.channel.send("No amount specified")
        try:
            amount = abs(int(amount))
        except ValueError:
            await ctx.channel.send("Wtf")
        donator = await players.get(ctx.author.id)
        acceptor = await players.get(user.id)
        await players.debit_money(donator, amount)
        await players.add_money(acceptor, amount)
        give_embed = discord.Embed(description=f"{donator.name} gave ${amount} to {acceptor.name}",
                                   colour=discord.Colour.gold())
        await ctx.channel.send(embed=give_embed)
