"""
This module contains the Player class, several methods to operate with players in the database and
the ActiveDrive, used to manage driving sessions
"""
from dataclasses import dataclass, field
import aiosqlite
import logging
import discord
import api.levels as levels
import api.items as items


async def init():
    global __con__
    __con__ = await aiosqlite.connect("./api/players.db")
    logging.info("Initialized player database")


async def close():
    await __con__.close()
    logging.info("Closed player database connection")


@dataclass
class Player:
    """
    Attributes:
        user_id: Unique discord user id to identify the player
        name: Displayed name in discord, NOT the Nickname
        level: players level
        xp: xp for current level
        money: Amount of ingame currency the player has
        position: Position on the 2 dimensional array that I call map
        miles: Amount of miles the Player has driven
    """

    user_id: int
    name: str
    level: int = 0
    xp: int = 0
    money: int = 0
    position: list = field(default_factory=lambda: [0, 0])
    miles: int = 0
    truck_miles: int = 0
    gas: int = 600
    truck_id: int = 0
    loaded_items: list = field(default_factory=lambda: [])


def __list_from_tuples(tups) -> list:
    """
    Returns a list with all Players generated from a set of tuples from the database
    """
    players = []
    for tup in tups:
        players.append(__from_tuple(tup))
    return players


def __from_tuple(tup: tuple) -> Player:
    """
    Returns a Player object from a received database tuple
    """
    return Player(
        tup[0],
        tup[1],
        tup[2],
        tup[3],
        tup[4],
        __get_position(tup[5]),
        tup[6],
        tup[7],
        tup[8],
        tup[9],
        __get_items(tup[10]),
    )


def __to_tuple(player: Player) -> tuple:
    """
    Transforms the player object into a tuple that can be inserted in the db
    """
    return (
        player.user_id,
        player.name,
        player.level,
        player.xp,
        player.money,
        __format_pos_to_db(player.position),
        player.miles,
        player.truck_miles,
        player.gas,
        player.truck_id,
        __format_items_to_db(player.loaded_items),
    )


def __get_position(db_pos: str) -> list:
    """
    Parses the position from the database as list [x][y]
    """
    pos_x = db_pos[: db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/") + 1:]
    return [int(pos_x), int(pos_y)]


def __format_pos_to_db(pos: list) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])


def __get_items(db_items: str) -> list:
    """
    Parses the item list from the db string
    """
    if db_items == "":
        return []
    player_items = []
    for item_name in db_items.split(";"):
        player_items.append(items.get(item_name))
    return player_items


def __format_items_to_db(item_list: list) -> str:
    """
    Returns a database-ready string containing all the items
    """
    db_items = ""
    for item in item_list:
        db_items += item.name + ";"
    # remove the last ;
    return db_items[: len(db_items) - 1]


async def add_xp(player: Player, amount: int) -> str:
    """
    Adds xp to the player and performs a level up if neede
    """
    answer = "\nYou got {:,} xp".format(amount)
    await update(player, xp=int(player.xp) + amount)
    while int(player.xp) >= levels.get_next_xp(player.level):
        await update(player, level=player.level + 1, xp=player.xp - levels.get_next_xp(player.level))
        answer += f"\n:tada: You leveled up to level {player.level} :tada:"
    return answer


async def add_money(player, amount) -> None:
    """
    Add money to the players account
    """
    await update(player, money=player.money + amount)


async def debit_money(player, amount) -> None:
    """
    Debit money from the players account
    """
    if amount > player.money:
        raise NotEnoughMoney()
    await update(player, money=player.money - amount)


async def load_item(player, item: items.Item) -> None:
    new_items = player.loaded_items
    new_items.append(item)
    await update(player, loaded_items=new_items)


async def unload_item(player, item: items.Item) -> None:
    new_items = player.loaded_items
    items_to_remove = []
    for loaded_item in new_items:
        if loaded_item.name == item.name:
            items_to_remove.append(loaded_item)

    for loaded_item in items_to_remove:
        new_items.remove(loaded_item)

    await update(player, loaded_items=new_items)


async def insert(player: Player) -> None:
    """
    Inserts a player into the database
    """
    await __con__.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?)", __to_tuple(player))
    await __con__.commit()
    logging.info("Inserted %s into the database as %s", player.name, __to_tuple(player))


async def remove(player: Player) -> None:
    """
    Removes a player from the database
    """
    await __con__.execute("DELETE FROM players WHERE id=:id", {"id": player.user_id})
    await __con__.commit()
    logging.info("Removed %s %s from the database", player.name, __to_tuple(player))


async def update(
    player: Player,
    name: str = None,
    level: int = None,
    xp: int = None,
    money: int = None,
    position: list = None,
    miles: int = None,
    truck_miles: int = None,
    gas: int = None,
    truck_id: int = None,
    loaded_items: list = None,
) -> None:
    """
    Updates a player in the database
    """
    if name is not None:
        await __con__.execute("UPDATE players SET name=? WHERE id=?", (name, player.user_id))
        player.name = name
    if level is not None:
        await __con__.execute("UPDATE players SET level=? WHERE id=?", (level, player.user_id))
        player.level = level
    if xp is not None:
        await __con__.execute("UPDATE players SET xp=? WHERE id=?", (xp, player.user_id))
        player.xp = xp
    if money is not None:
        await __con__.execute("UPDATE players SET money=? WHERE id=?", (money, player.user_id))
        player.money = money
    if position is not None:
        await __con__.execute(
            "UPDATE players SET position=? WHERE id=?", (__format_pos_to_db(position), player.user_id)
        )
        player.position = position
    if miles is not None:
        await __con__.execute("UPDATE players SET miles=? WHERE id=?", (miles, player.user_id))
        player.miles = miles
    if truck_miles is not None:
        await __con__.execute("UPDATE players SET truck_miles=? WHERE id=?", (truck_miles, player.user_id))
        player.truck_miles = truck_miles
    if gas is not None:
        await __con__.execute("UPDATE players SET gas=? WHERE id=?", (gas, player.user_id))
        player.gas = gas
    if truck_id is not None:
        await __con__.execute("UPDATE players SET truck_id=? WHERE id=?", (truck_id, player.user_id))
        player.truck_id = truck_id
    if loaded_items is not None:
        await __con__.execute(
            "UPDATE players SET loaded_items=? WHERE id=?", (__format_items_to_db(loaded_items), player.user_id)
        )
        player.loaded_items = loaded_items
    await __con__.commit()
    logging.debug("Updated player %s to %s", player.name, __to_tuple(player))


async def get(user_id: int) -> Player:
    """
    Get one player from the database
    """
    if not await registered(user_id):
        raise PlayerNotRegistered(user_id)
    cur = await __con__.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    player_tuple = await cur.fetchone()
    await cur.close()
    return __from_tuple(player_tuple)


async def get_top(key) -> tuple:
    """
    Get the top 10 players from the database
    """
    if key == "money":
        cur = await __con__.execute("SELECT * FROM players ORDER BY money DESC")
        suffix = "$"
    elif key == "miles":
        cur = await __con__.execute("SELECT * FROM players ORDER BY miles DESC")
        suffix = " miles"
    else:
        cur = await __con__.execute("SELECT * FROM players ORDER BY level DESC, xp DESC")
        suffix = ""
    top_tuples = await cur.fetchmany(10)
    await cur.close()
    return __list_from_tuples(top_tuples), suffix


async def registered(user_id: int) -> bool:
    """
    Checks whether a specific user is registered or not
    """
    cur = await __con__.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    if len(await cur.fetchall()) == 1:
        await cur.close()
        return True
    await cur.close()
    return False


async def get_count() -> int:
    """
    Returns the player count
    """
    cur = await __con__.execute("SELECT COUNT(*) FROM players")
    number_tuple = await cur.fetchall()
    await cur.close()
    return number_tuple[0][0]


@dataclass
class ActiveDrive:
    """
    Object to manage current driving session and prevent duplicate driving
    Attributes:
        player: Player object of the driving player
        message: Discord message where the drive is displayed and where the reactions are
        last_action_time: Time used to keep the list clean and time out drives
    """

    player: Player
    message: discord.Message
    last_action_time: float


class PlayerNotRegistered(Exception):
    """
    Exception raised when a player that is not registered is requested
    """

    def __init__(self, requested_id, *args: object) -> None:
        self.requested_id = requested_id
        super().__init__(*args)

    def __str__(self) -> str:
        return f"The requested player ({self.requested_id}) is not registered"


class NotEnoughMoney(Exception):
    """
    Exception raised when more money is withdrawn than the player has
    """

    def __str__(self) -> str:
        return "The requested player doesn't have enough money to perform this action"
