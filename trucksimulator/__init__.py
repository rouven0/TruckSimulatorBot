"Main service file that is loaded into gunicorn"
# pylint: disable=unused-argument
import logging
import sys
import traceback
from os import getenv

from trucksimulator import config
import i18n
from flask import Flask, json, request, send_file
from flask_discord_interactions import Context, DiscordInteractions, Message
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.embed import Embed, Footer
from i18n import set as set_i18n
from i18n import t
from trucksimulator.resources import players
from werkzeug.exceptions import HTTPException

i18n.set("filename_format", config.I18n.FILENAME_FORMAT)
i18n.set("fallback", config.I18n.FALLBACK)
i18n.set("available_locales", config.I18n.AVAILABLE_LOCALES)
i18n.set("skip_locale_root_data", True)
i18n.load_path.append(config.BASE_PATH + "/locales")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)

app = Flask(__name__)


@app.route("/robots.txt")
def get_robots():
    return send_file(f"{config.BASE_PATH}/robots.txt")


@app.route("/health")
def health():
    return "OK"


class CustomDiscordInteractions(DiscordInteractions):
    def handle_request(self):
        set_i18n("locale", request.json.get("locale"))
        return super().handle_request()

    def run_command(self, data: dict):
        ctx = Context.from_data(self, app, data)
        logging.info(
            "%s#%s used /%s in guild %s with locale %s.",
            ctx.author.username,
            ctx.author.discriminator,
            ctx.command_name,
            ctx.guild_id,
            ctx.locale,
        )
        return super().run_command(data)


discord = CustomDiscordInteractions(app)

app.config["DISCORD_CLIENT_ID"] = getenv("DISCORD_CLIENT_ID", default="")
app.config["DISCORD_PUBLIC_KEY"] = getenv("DISCORD_PUBLIC_KEY", default="")
app.config["DISCORD_CLIENT_SECRET"] = getenv("DISCORD_CLIENT_SECRET", default="")

if "--debug" in sys.argv:
    app.config["DONT_VALIDATE_SIGNATURE"] = True


# ugly thing I have to do to support nested locales
for locale in config.I18n.AVAILABLE_LOCALES:
    logging.info("Initialized locale %s", locale)
    i18n.t("name", locale=locale)


def dump(message: Message) -> dict:
    """Dumps a message as json to send raw data back to discord"""
    return json.loads(message.encode()[0])


@app.errorhandler(players.NotEnoughMoney)
def not_enough_money(error):
    """Error handler in case a player doesn't have enough money"""
    return dump(Message(content=t("errors.not_enough_money.message"), ephemeral=True))


@app.errorhandler(players.WrongPlayer)
def not_driving(error):
    """Defer buttons if the wrong player clicked them"""
    required_permissions = [
        10,
        11,
        31,
    ]  # view_channels, send_messages, use_application_commands
    if all([int(request.json.get("member").get("permissions")) & (1 << n) for n in required_permissions]):
        return dump(
            Message(
                t("errors.not_driving.driving_allowed.message"),
                ephemeral=True,
                components=[
                    ActionRow(
                        components=[
                            Button(
                                label=t("errors.not_driving.driving_allowed.cta"),
                                style=2,
                                custom_id="initial_drive",
                                emoji={"name": "logo_round", "id": 955233759278559273},
                            )
                        ]
                    )
                ],
            )
        )
    return dump(Message(t("errors.not_driving.driving_forbidden.message"), ephemeral=True))


@app.errorhandler(players.PlayerNotRegistered)
def not_registered(error):
    """Error handler in case a player isn't found in the database"""
    interaction_data = request.json
    author = (
        interaction_data.get("member").get("user").get("id")
        if interaction_data.get("member", None)
        else interaction_data.get("user").get("id")
    )
    if author == error.requested_id:
        content = t("errors.not_registered.self.message", player_id=error.requested_id)
        components = [
            ActionRow(
                components=[
                    Button(
                        label=t("errors.not_registered.self.cta"),
                        custom_id=["profile_register", error.requested_id],
                    )
                ]
            )
        ]
    else:
        content = t("errors.not_registered.other.message", player_id=error.requested_id)
        components = []

    return dump(
        Message(
            content=content,
            components=components,
        )
    )


@app.errorhandler(players.PlayerBlacklisted)
def blacklisted(error: players.PlayerBlacklisted):
    """Error handler in case a player is on the blalist"""
    return dump(
        Message(
            t(
                "errors.blacklisted.message",
                player_id=error.requested_id,
                reason=error.reason,
            ),
            ephemeral=True,
        )
    )


@app.errorhandler(Exception)
def general_error(error):
    """Log any error to journal and to discord"""
    logging.error(error)
    traceback.print_tb(error.__traceback__)
    return dump(
        Message(
            embed=Embed(
                title="Looks like we got an error here.",
                description=f" ```py\n {error.__class__.__name__}: {error}```",
                footer=Footer(
                    text="If this occurs multiple times feel free to report it.",
                    icon_url=config.SELF_AVATAR_URL,
                ),
                color=int("ff0000", 16),
            ),
            components=[
                ActionRow(
                    components=[
                        Button(
                            style=5,
                            label="Support Server",
                            url="https://discord.gg/FzAxtGTUhN",
                        )
                    ]
                )
            ],
        )
    )


@app.errorhandler(HTTPException)
def handle_exception(error):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = error.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "code": error.code,
            "name": error.name,
            "description": error.description,
        }
    )
    response.content_type = "application/json"
    return response


if "--remove-global" in sys.argv:
    discord.update_commands()
    sys.exit()

if "--clear-admin" in sys.argv:
    discord.update_commands(guild_id=config.Guilds.SUPPORT)
    sys.exit()

from trucksimulator.admin import admin_bp

if "--admin" in sys.argv:
    discord.register_blueprint(admin_bp)
    discord.update_commands(guild_id=config.Guilds.SUPPORT)
    sys.exit()

from trucksimulator.companies import company_bp
from trucksimulator.driving import driving_bp
from trucksimulator.economy import economy_bp
from trucksimulator.gambling import gambling_bp
from trucksimulator.guide import guide_bp
from trucksimulator.stats import profile_bp
from trucksimulator.system import system_bp
from trucksimulator.truck import truck_bp

discord.register_blueprint(system_bp)
discord.register_blueprint(profile_bp)
discord.register_blueprint(driving_bp)
discord.register_blueprint(economy_bp)
discord.register_blueprint(gambling_bp)
discord.register_blueprint(guide_bp)
discord.register_blueprint(truck_bp)
discord.register_blueprint(company_bp)


if "--deploy" in sys.argv:
    discord.update_commands()
    sys.exit()


@discord.command()
def complain(ctx) -> str:
    "No description."
    return i18n.t("complain.response", locale=ctx.locale)


discord.register_blueprint(admin_bp)


discord.set_route("/interactions")


if __name__ == "__main__":
    app.run(port=9001, debug=True)
