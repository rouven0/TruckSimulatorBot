"Blueprint file containing the info command and some general button handlers for abort and back buttons"
# pylint: disable=unused-argument, missing-function-docstring
from datetime import datetime
from math import floor

import config
from flask_discord_interactions import Context, DiscordInteractionsBlueprint, Embed, Message
from flask_discord_interactions.models.component import ActionRow, Button, ButtonStyles
from flask_discord_interactions.models.embed import Field, Footer, Media
from resources import players
from utils import log_command

# remove this as soon as locales are in ctx
from flask import request
from i18n import t, set as set_i18n

start_time = datetime.now()

system_bp = DiscordInteractionsBlueprint()


def get_info_embed() -> Embed:
    info_embed = Embed(
        title="Truck Simulator Info",
        color=config.EMBED_COLOR,
        footer=Footer(text=t("info.developer")),
        thumbnail=Media(url=config.SELF_AVATAR_URL),
        timestamp=datetime.utcnow().replace(microsecond=0).isoformat(),
    )

    uptime = datetime.now() - start_time
    days = uptime.days
    hours = floor(uptime.seconds / 3600)
    minutes = floor(uptime.seconds / 60) - hours * 60
    seconds = uptime.seconds - hours * 3600 - minutes * 60

    info_embed.fields = [
        Field(
            name=t("info.system.title"),
            value=t(
                "info.system.text",
                uptime=f"{days}d {hours}h {minutes}m {seconds}s",
                players=players.get_count("players"),
                jobs=players.get_count("jobs"),
                companies=players.get_count("companies"),
            ),
            inline=False,
        ),
        Field(name=t("info.credits.title"), value=t("info.credits.text"), inline=False),
    ]
    return info_embed


@system_bp.command()
def info(ctx: Context) -> Message:
    """Prints out general information about this app."""
    set_i18n("locale", request.json.get("locale"))
    log_command(ctx)
    return Message(
        embed=get_info_embed(),
        components=[
            ActionRow(
                components=[
                    Button(style=5, url=link["url"], label=link["name"], emoji=link.get("emoji"))
                    for link in config.info_links()
                ]
            ),
            ActionRow(
                components=[
                    Button(
                        style=ButtonStyles.SECONDARY,
                        label=t("info.refresh"),
                        custom_id=str(refresh),
                        emoji={"name": "reload", "id": 903581225149665290},
                    )
                ]
            ),
        ],
    )


@system_bp.custom_handler(custom_id="refresh_system_info")
def refresh(ctx: Context):
    set_i18n("locale", request.json.get("locale"))
    return Message(embed=get_info_embed(), update=True)
