"""
Some utility functions
"""

import logging

from flask_discord_interactions.context import Context


def log_command(ctx: Context) -> None:
    """
    Log a used command to stdout
    """
    logging.info(
        "%s#%s used /%s in guild %s", ctx.author.username, ctx.author.discriminator, ctx.command_name, ctx.guild_id
    )


def commatize(i: int) -> str:
    """
    Comma-formats a number
    Example:
    ----
        1000000 -> 1,000,000
    """
    return f"{i:,}"
