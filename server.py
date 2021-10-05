"""
Support server actions
"""

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import (
    create_button,
    create_actionrow,
    create_select,
    create_select_option,
    ComponentContext,
)

import api.players as players
import api.jobs as jobs


class Server(commands.Cog):
    """
    All server commands and components
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @cog_ext.cog_subcommand(base="support", subcommand_group="profile", guild_ids=[839580174282260510])
    async def delete(self, ctx) -> None:
        """
        Delete your account
        """
        await players.get(ctx.author.id)
        await ctx.send(
            "Are you sure you want to delete your profile? **All your ingame stats will be lost!**",
            hidden=True,
            components=[
                create_actionrow(
                    create_button(style=3, label="Yes", custom_id="confirm_deletion"),
                    create_button(style=4, label="No", custom_id="abort_deletion"),
                )
            ],
        )

    @cog_ext.cog_component()
    async def confirm_deletion(self, ctx: ComponentContext):
        player = await players.get(ctx.author.id)
        await players.remove(player)
        job = jobs.get(ctx.author.id)
        if job is not None:
            jobs.remove(job)
        await ctx.edit_origin(components=[])
        await ctx.send("Your profile got deleted. We will miss you :(", hidden=True)

    @cog_ext.cog_component()
    async def abort_deletion(self, ctx: ComponentContext):
        await ctx.edit_origin(content="Deletion aborted", components=[])

    @cog_ext.cog_slash(guild_ids=[839580174282260510])
    async def serverrules(self, ctx) -> None:
        """
        Truck Simulator server rules
        """
        rules_embed = discord.Embed(title="Truck Simulator Server Rules", colour=discord.Colour.gold())
        rules_embed.add_field(
            name="Be civil and respectful",
            value="Treat everyone with respect. Absolutely no harassment, witch hunting, sexism, racism, "
            "or hate speech will be tolerated.",
            inline=False,
        )
        rules_embed.add_field(
            name="No spam or self-promotion",
            value="No spam or self-promotion (server invites, advertisements, etc) without permission "
            "from a staff member. This includes DMing fellow members.",
            inline=False,
        )
        rules_embed.add_field(
            name="No NSFW or obscene content",
            value="This includes text, images, or links featuring nudity, sex, hard violence, "
            "or other graphically disturbing content.",
            inline=False,
        )
        await ctx.send(embed=rules_embed)

    @cog_ext.cog_slash(guild_ids=[839580174282260510])
    async def roles(self, ctx):
        """
        Grab yourself some neat roles here
        """
        components = [
            create_actionrow(
                create_select(
                    custom_id="select_roles",
                    placeholder="Select your roles",
                    min_values=0,
                    max_values=2,
                    options=[
                        create_select_option(
                            label="Annoucements",
                            value="870298899129196574",
                            description="Get notified when the bot is updated",
                            emoji="📣",
                            default=(870298899129196574 in [r.id for r in ctx.author.roles]),
                        ),
                        create_select_option(
                            label="Events",
                            value="894885560164974593",
                            description="Get notified for ingame events",
                            emoji="📆",
                            default=(894885560164974593 in [r.id for r in ctx.author.roles]),
                        ),
                    ],
                )
            )
        ]
        embed = discord.Embed(
            description="Select your ping roles down below. All roles you selectet will be given to you, all roles you didn't select will be removed from you.",
            colour=discord.Colour.gold(),
        )
        embed.set_author(name="Select your roles", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed, components=components, hidden=True)

    @cog_ext.cog_component()
    async def select_roles(self, ctx: ComponentContext) -> None:
        roles_to_remove = [870298899129196574, 894885560164974593]
        for role in ctx.selected_options:
            roles_to_remove.remove(int(role))
        await ctx.author.remove_roles(
            *[ctx.guild.get_role(int(i)) for i in roles_to_remove], reason="Role selection via /role"
        )
        await ctx.author.add_roles(
            *[ctx.guild.get_role(int(i)) for i in ctx.selected_options], reason="Role selection via /role"
        )
        await ctx.defer(ignore=True)
