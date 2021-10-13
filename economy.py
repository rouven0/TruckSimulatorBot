"""
This module contains the Cog for all economy-related commands
"""
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import ComponentContext
import api.players as players
import api.places as places
import api.items as items
import api.jobs as jobs
import api.symbols as symbols
import api.trucks as trucks


class Economy(commands.Cog):
    """
    Earn money, trade it and buy better Trucks
    """

    def __init__(self, bot: commands.Bot, driving_commands) -> None:
        self.bot = bot
        self.driving_commands = driving_commands
        super().__init__()

    @cog_ext.cog_component()
    async def show_job(self, ctx: ComponentContext) -> None:
        """
        Shows your current job
        """
        active_drive = self.driving_commands.get_active_drive(ctx.author_id, ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return

        current_job = await active_drive.player.get_job()
        job_embed = discord.Embed(colour=discord.Colour.lighter_grey())
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

    @cog_ext.cog_slash()
    async def minijobs(self, ctx):
        """
        Prints out all permanently running minijobs
        """
        player = await players.get(ctx.author.id)
        minijob_list = ""
        for place in places.get_all():
            if place.accepted_item is not None:
                minijob_list += f"\n{symbols.LIST_ITEM}**{place.name}** will give you ${place.item_reward*(player.level+1):,} if you bring them *{place.accepted_item}*."
        await ctx.send(
            embed=discord.Embed(
                title="All available minijobs", description=minijob_list, colour=discord.Colour.lighter_grey()
            )
        )

    @cog_ext.cog_component()
    async def new_job(self, ctx: ComponentContext) -> None:
        """
        Get a new job
        """
        active_drive = self.driving_commands.get_active_drive(ctx.author_id, ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return
        job_embed = discord.Embed(colour=discord.Colour.lighter_grey())
        job_embed.set_author(name="{}'s Job".format(ctx.author.name), icon_url=ctx.author.avatar_url)
        job = jobs.generate(active_drive.player)
        await active_drive.player.add_job(job)
        item = items.get(job.place_from.produced_item)
        job_message = "{} needs {} {} from {}. You get ${:,} for this transport".format(
            job.place_to.name, self.bot.get_emoji(item.emoji), item.name, job.place_from.name, job.reward
        )
        job_embed.add_field(name="You got a new Job", value=job_message, inline=False)
        job_embed.add_field(name="Current state", value=jobs.get_state(job))
        await ctx.edit_origin(
            embed=await self.driving_commands.get_drive_embed(active_drive.player, ctx.author.avatar_url),
            components=await self.driving_commands.get_buttons(active_drive.player),
        )
        await ctx.send(embed=job_embed, hidden=True)

    @cog_ext.cog_component()
    async def refill(self, ctx: ComponentContext):
        """
        If you're at the gas station, you can refill your truck's gas
        """
        active_drive = self.driving_commands.get_active_drive(ctx.author_id, ctx.origin_message_id)
        if active_drive is None:
            await ctx.defer(ignore=True)
            return
        gas_amount = trucks.get(active_drive.player.truck_id).gas_capacity - active_drive.player.gas
        price = round(gas_amount * 1.2)

        try:
            await active_drive.player.debit_money(price)
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
            colour=discord.Colour.lighter_grey(),
        )
        refill_embed.set_footer(text="Current gas price: $1.2 per litre")
        await players.update(active_drive.player, gas=trucks.get(active_drive.player.truck_id).gas_capacity)
        await ctx.edit_origin(
            embed=await self.driving_commands.get_drive_embed(active_drive.player, ctx.author.avatar_url)
        )
        await ctx.send(embed=refill_embed, hidden=True)

    @cog_ext.cog_slash()
    async def give(self, ctx, user: discord.User, amount: int) -> None:
        """
        Do I really have to explain this?
        """
        amount = abs(int(amount))
        if isinstance(user, str):
            acceptor = await players.get(int(user))
        else:
            acceptor = await players.get(user.id)
        if ctx.author.id == 692796548282712074:
            await acceptor.add_money(amount)
            await ctx.send(
                embed=discord.Embed(
                    description=f"${amount} were given to {acceptor.name}",
                    colour=discord.Colour.lighter_grey(),
                )
            )
            return

        donator = await players.get(ctx.author.id)
        if ctx.author.id == acceptor.user_id:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Hey {ctx.author.name}",
                    description="You can't give money to yourself!",
                    colour=discord.Colour.lighter_grey(),
                )
            )
            return
        if donator.level < 1:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Hey {ctx.author.name}",
                    description="You have to be at least level 1 to give money!",
                    colour=discord.Colour.lighter_grey(),
                )
            )
            return
        await donator.debit_money(amount)
        await acceptor.add_money(amount)
        await ctx.send(
            embed=discord.Embed(
                description=f"{donator.name} gave ${amount} to {acceptor.name}", colour=discord.Colour.lighter_grey()
            )
        )
