"""
Tis module contains the Cog for all gambling-related commands
"""
from random import randint

from discord.ext import commands

import players
import places


class Gambling(commands.Cog):
    """
    Lose your money here
    """
    @commands.command(aliases=["cf"])
    async def coinflip(self, ctx, side=None, amount=None) -> None:
        """
        Test your luck while throwing a coin
        """
        player = players.get(ctx.author.id)
        if "coinflip" in places.get(player.position).commands:
            try:
                if amount == "all":
                    amount = player.money
                elif amount == "half":
                    amount = round(player.money / 2)
                else:
                    amount = int(amount)

                if str.lower(side) not in ["h", "head", "t", "tails"]:
                    await ctx.channel.send("**Syntax:** `t.coinflip [h/t] <amount>`")
                    return

                if side == "h":
                    side = "heads"
                elif side == "t":
                    side = "tails"
                players.debit_money(player, amount)
                if randint(0, 1) == 0:
                    result = "heads"
                else:
                    result = "tails"

                if result == side:
                    await ctx.channel.send("Congratulations, it was {}. You won ${}".format(result, amount))
                    players.add_money(player, amount*2)
                else:
                    await ctx.channel.send("Nope, it was {}. You lost ${}".format(result, amount))
            except (IndexError, ValueError):
                await ctx.channel.send("**Syntax:** `t.coinflip [h/t] <amount>`")
        else:
            await ctx.channel.send("We are not in Las Vegas!!!")
