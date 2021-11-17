"""
This module contains the Cog for all company-related commands
"""

import re
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import (
    create_button,
    create_actionrow,
    ComponentContext,
    wait_for_component,
)

import api.players as players
import api.places as places
import api.companies as companies
from aiosqlite import IntegrityError


class Companies(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @cog_ext.cog_subcommand(base="company")
    async def found(self, ctx, name: str):
        """
        Create a company
        """
        if not re.match("^[a-zA-Z]", name):
            await ctx.send("Bad name. Company names must start with a letter")
            return

        player = await players.get(ctx.author.id)
        if player.company is not None:
            await ctx.send("You already have a company. You can't found another one!")
            return
        if player.position in [p.position for p in places.get_all()] or player.position in [
            c.hq_position for c in await companies.get_all()
        ]:
            await ctx.send("You can't found a company on this position, please drive to an empty field.")
            return

        confirm_embed = discord.Embed(
            title="Confirm your guild creation",
            description=f"Please confirm that you want to found the company **{name}** as position {player.position}. "
            "This position is final, can not be changed and "
            "your company's logo will appear on this position on the map everyone can see.",
            colour=discord.Colour.light_grey(),
        )
        confirm_buttons = [
            create_actionrow(
                create_button(style=3, label="Confirm", custom_id="confirm_company_found"),
                create_button(style=4, label="Cancel", custom_id="cancel_company_found"),
            )
        ]

        confirm_embed.set_author(name=f"{player.name}'s company", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=confirm_embed, components=confirm_buttons, hidden=True)

        confirm: ComponentContext = await wait_for_component(self.bot, components=confirm_buttons, timeout=30)
        if confirm.custom_id == "confirm_company_found":
            try:
                company = companies.Company(name, f":regional_indicator_{name[0]}:", player.position, ctx.author.id, 0)
                await companies.insert(company)
                await players.update(player, company=name)
                await ctx.send(
                    embed=discord.Embed(
                        title="Company creation successful",
                        description=f"{company.logo} **{company.name}** has been created and placed in the market. "
                        f"Your company's headquarters have been built at {company.hq_position}.\n"
                        "To change your logo run `/company update logo`",
                        colour=discord.Colour.light_grey(),
                    )
                )
            except IntegrityError:
                await ctx.send("A company with this make already exists, please choose another name")
        await confirm.edit_origin(components=[])

    @cog_ext.cog_subcommand(base="company")
    async def hire(self, ctx, user: discord.User):
        player = await players.get(ctx.author.id)
        if isinstance(user, str):
            invited_player = await players.get(int(user))
        else:
            invited_player = await players.get(user.id)
        company = await companies.get(player.company)
        if ctx.author.id != company.founder:
            await ctx.send("You are not the company founder!")
            return
        # TODO add confirmation of invited player
        if invited_player.company is None:
            await players.update(invited_player, company=company.name)
            await ctx.send("Done")
        else:
            await ctx.send(
                f"**{invited_player.name}** you are already member of a company. Leave that one before you join a new one"
            )

    @cog_ext.cog_subcommand(
        base="company", subcommand_group="update", subcommand_group_description="Make changes to your company"
    )
    async def logo(self, ctx, logo):
        player = await players.get(ctx.author.id)
        if re.match("<a*:\\w*:\\d*>", logo):
            company = await companies.get(player.company)
            if ctx.author.id != company.founder:
                await ctx.send("You are not the company founder!")
                return
            await companies.update(company, logo=logo)
            await ctx.send(f"Done. Your company logo was set to {logo}")
        else:
            await ctx.send("That's not an emoji")


def setup(bot):
    bot.add_cog(Companies(bot))
