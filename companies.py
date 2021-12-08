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
                company = companies.Company(
                    name, f":regional_indicator_{str.lower(name[0])}:", player.position, ctx.author.id, 3000
                )
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
        """
        Get a new player into your company
        """
        player = await players.get(ctx.author.id)
        if isinstance(user, str):
            invited_player = await players.get(int(user))
        else:
            invited_player = await players.get(user.id)
        company = await companies.get(player.company)
        if ctx.author.id != company.founder:
            await ctx.send("You are not the company founder!")
            return
        if invited_player.company is not None:
            await ctx.send(f"**{invited_player.name}** already is member of a company.")
            return

        confirm_buttons = [
            create_actionrow(
                create_button(style=3, label="Confirm", custom_id="confirm_company_hire"),
                create_button(style=4, label="Cancel", custom_id="cancel_company_hire"),
            )
        ]
        await ctx.send(
            f"<@{invited_player.user_id}> **{player.name}** wants to hire you for their company. "
            f"Please confirm that you want to work for {company.logo} **{company.name}**",
            components=confirm_buttons,
        )
        confirm: ComponentContext = await wait_for_component(
            self.bot, components=confirm_buttons, check=lambda i: i.author.id == invited_player.user_id, timeout=30
        )

        if confirm.custom_id == "confirm_company_hire":
            await ctx.send(
                f"It's official! **{invited_player.name}** is now a member of **{company.name}** <:PandaHappy:869202868555624478>"
            )
            await players.update(invited_player, company=company.name)
        await confirm.edit_origin(components=[])

    @cog_ext.cog_subcommand(base="company")
    async def fire(self, ctx, user: discord.User):
        """
        Remove a player from your company
        """
        player = await players.get(ctx.author.id)
        if isinstance(user, str):
            fired_player = await players.get(int(user))
        else:
            fired_player = await players.get(user.id)
        company = await companies.get(player.company)
        if ctx.author.id != company.founder:
            await ctx.send("You are not the company founder!")
            return
        if fired_player.company is not company.name:
            await ctx.send(f"**{fired_player.name}** is not a member of your company.")
            return

        confirm_buttons = [
            create_actionrow(
                create_button(style=3, label="Yes", custom_id="confirm_company_fire"),
                create_button(style=4, label="No", custom_id="cancel_company_fire"),
            )
        ]
        await ctx.send(
            f"Are you sure you want to remove {fired_player.name} from **{company.name}**?",
            components=confirm_buttons,
            hidden=True,
        )
        confirm: ComponentContext = await wait_for_component(self.bot, components=confirm_buttons, timeout=30)

        if confirm.custom_id == "confirm_company_fire":
            await ctx.send(f"**{fired_player.name}** was removed from **{company.name}**")
            await fired_player.remove_from_company()
        await confirm.edit_origin(components=[])

    @cog_ext.cog_subcommand(base="company")
    async def leave(self, ctx):
        """
        Leave your company
        """
        player = await players.get(ctx.author.id)
        if player.company is None:
            await ctx.send("You don't have company to leave!")
            return
        company = await companies.get(player.company)
        if ctx.author.id == company.founder:
            await ctx.send("You can't leave the company you founded!")
            return
        confirm_buttons = [
            create_actionrow(
                create_button(style=3, label="Yes", custom_id="confirm_company_leave"),
                create_button(style=4, label="No", custom_id="cancel_company_leave"),
            )
        ]
        await ctx.send("Are you sure that you want to leave your company?", components=confirm_buttons, hidden=True)
        confirm: ComponentContext = await wait_for_component(self.bot, components=confirm_buttons, timeout=30)
        if confirm.custom_id == "confirm_company_leave":
            await ctx.send(f"<@{player.user_id}> You left **{player.company}**")
            await player.remove_from_company()
        await confirm.edit_origin(components=[])

    @cog_ext.cog_subcommand(
        base="company", subcommand_group="update", subcommand_group_description="Make changes to your company"
    )
    async def logo(self, ctx, logo):
        """
        Change your company's logo
        """
        await ctx.defer()
        # logo = logo.encode("unicode-escape").decode("ASCII")
        player = await players.get(ctx.author.id)
        if re.match(
            # did I mention that I love regex?
            # match any emoji
            r"^([\u2600-\u26ff]|[\U0001f000-\U0001faff])|<a*:\w*:\d+>$",
            logo,
        ):
            company = await companies.get(player.company)
            if ctx.author.id != company.founder:
                await ctx.send("You are not the company founder!")
                return
            await companies.update(company, logo=logo)
            await ctx.send(
                f"Done. Your company logo was set to {logo} Please note that your logo can be reset at any time if it is found not working or inappropriate"
            )
        else:
            await ctx.send("That's not an emoji")

    @cog_ext.cog_subcommand(base="company")
    async def show(self, ctx, user: discord.User = None):
        """
        Show details about your company
        """
        if isinstance(user, str):
            user = await self.bot.fetch_user(int(user))
        if user is not None:
            target_user = user
        else:
            target_user = ctx.author
        player = await players.get(target_user.id)
        try:
            company = await companies.get(player.company)
        except companies.CompanyNotFound:
            begin = "You are " if user is None else f"{user.name} is "
            await ctx.send(begin + "not member of a company at the moment", hidden=True)
            return
        founder = self.bot.get_user(company.founder)
        if founder is None:
            await ctx.defer()
            founder = await self.bot.fetch_user(company.founder)
        company_embed = discord.Embed(title=company.name, colour=discord.Colour.lighter_grey())
        company_embed.set_author(name=f"{player.name}'s company", icon_url=target_user.avatar_url)
        logo_id = company.logo[company.logo.find(":", 2) + 1 : company.logo.find(">")]
        company_embed.set_thumbnail(url=f"https://cdn.discordapp.com/emojis/{logo_id}.png")
        company_embed.set_footer(text=f"Founded by {founder.name}#{founder.discriminator}", icon_url=founder.avatar_url)
        company_embed.add_field(name="Headquarters position", value=company.hq_position)
        company_embed.add_field(name="Net worth", value=f"${company.net_worth}", inline=False)
        members = ""
        for member in await company.get_members():
            members += f"{member.name} \n"
        company_embed.add_field(name="Members", value=members, inline=False)
        await ctx.send(embed=company_embed)


def setup(bot):
    bot.add_cog(Companies(bot))
