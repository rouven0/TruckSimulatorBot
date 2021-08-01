"""
Tis module contains the Cog for all gambling-related commands
"""
from random import randint, sample, choices
import discord

from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

import players
import places
import items


class Gambling(commands.Cog):
    """
    Lose your money here
    """
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @cog_ext.cog_slash(
            options=[
                create_option(
                    name="side",
                    description="The side you bet on",
                    option_type=3,
                    choices=["heads", "tails"],
                    required=True),
                create_option(
                    name="amount",
                    description="The amount you bet",
                    option_type=10,
                    required=True) ])

    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def coinflip(self, ctx, side: str, amount:int) -> None:
        """
        Test your luck while throwing a coin
        """
        player = await players.get(ctx.author.id)
        if "coinflip" not in places.get(player.position).commands:
            raise places.WrongPlaceError("We are not in Las Vegas!!!")

        await players.debit_money(player, amount)
        if randint(0, 1) == 0:
            result = "heads"
        else:
            result = "tails"

        if result == side:
            await ctx.send("Congratulations, it was {}. You won ${}".format(result, "{:,}".format(amount)))
            await players.add_money(player, amount*2)
        else:
            await ctx.send("Nope, it was {}. You lost ${}".format(result, "{:,}".format(amount)))

    @cog_ext.cog_slash()
    @commands.bot_has_permissions(view_channel=True, send_messages=True,
                                  embed_links=True, attach_files=True, read_message_history=True,
                                  use_external_emojis=True)
    async def slots(self, ctx, amount:int) -> None:
        """
        Simple slot machine
        """
        player = await players.get(ctx.author.id)
        if "slots" not in places.get(player.position).commands:
            raise places.WrongPlaceError("We are not in Las Vegas!!!")
        await players.debit_money(player, amount)

        chosen_items = choices(sample(items.get_all(), 8), k=3)
        machine = "<|"
        for item in chosen_items:
            machine += str(self.bot.get_emoji(item.emoji))
            machine += "|"
        machine += ">"

        slots_embed = discord.Embed(description=machine, colour=discord.Colour.gold())
        slots_embed.set_author(name=f"{ctx.author.name}'s slots", icon_url=ctx.author.avatar_url)

        if chosen_items.count(chosen_items[0]) == 3:
            slots_embed.add_field(name="Result", value=":tada: Congratulations, you won {:,} :tada:".format(amount*10))
            await players.add_money(player, amount*11)
        elif chosen_items.count(chosen_items[0]) == 2 or chosen_items.count(chosen_items[1]) == 2:
            slots_embed.add_field(name="Result", value="You won ${:,}".format(amount))
            await players.add_money(player, amount*2)
        else:
            slots_embed.add_field(name="Result", value="You lost ${:,}".format(amount))
        await ctx.send(embed=slots_embed)
