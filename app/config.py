# pylint: disable=too-few-public-methods
"Some configuration values"
from os import getenv


MAP_BORDER = 25
LOG_FORMAT = "%(levelname)s [%(module)s.%(funcName)s]: %(message)s"
EMBED_COLOR = int("0x918888", 16)
SELF_AVATAR_URL = "https://cdn.discordapp.com/avatars/831052837353816066/c9b904f935580ac68f54f184f6fc620c.png"

DATABASE_ARGS = {
    "host": getenv("MYSQL_HOST"),
    "user": getenv("MYSQL_USER"),
    "passwd": getenv("MYSQL_PASSWORD"),
    "database": getenv("MYSQL_DATABASE"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "use_unicode": True,
}


class Guilds:
    "Guild id used for command registration"
    SUPPORT = "839580174282260510"


class Users:
    "User ids to determine some important roles"
    ADMIN = "692796548282712074"
