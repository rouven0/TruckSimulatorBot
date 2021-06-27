"""
This module contains the Cog for all economy-related commands
"""
from random import randint
import discord
from discord.ext import commands
import players
import jobs


class Economy(commands.Cog):
    """
    Earn money, trade it and buy better Trucks
    """

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
            players.update(player, money=player.money + current_job.reward)
        else:
            await ctx.channel.send("Nothing to do here")

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
