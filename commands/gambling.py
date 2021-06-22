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
    async def coinflip(self, ctx, *args):
        """
        Test your luck while throwing a coin
        """
        player = players.get(ctx.author.id)
        if "coinflip" in places.get(player.position).commands:
            try:
                if args[1] == "all":
                    amount = player.money
                elif args[1] == "half":
                    amount = round(player.money / 2)
                else:
                    amount = int(args[1])

                if args[0] == "h":
                    side = "heads"
                elif args[0] == "t":
                    side = "tails"
                else:
                    await ctx.channel.send("**Syntax:** `t.coinflip [h/t] <amount>`")
                    return
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
