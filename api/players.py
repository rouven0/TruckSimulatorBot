"""
This module contains the Player class, several methods to operate with players in the database and
the ActiveDrive, used to manage driving sessions
"""
from dataclasses import dataclass
from typing import Union
import aiosqlite
import logging
import discord
import api.levels as levels
import api.items as items


def _format_pos_to_db(pos: list) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])


def _format_items_to_db(item_list: list) -> str:
    """
    Returns a database-ready string containing all the items
    """
    db_items = ""
    for item in item_list:
        db_items += item.name + ";"
    # remove the last ;
    return db_items[: len(db_items) - 1]


async def init():
    global __con__
    __con__ = await aiosqlite.connect("./api/players.db")
    logging.info("Initialized player database")


async def close():
    await __con__.close()
    logging.info("Closed player database connection")


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

    def __init__(
        self,
        user_id: int,
        name: str,
        level: int = 0,
        xp: int = 0,
        money: int = 0,
        position: Union[list, str] = [0, 0],
        miles: int = 0,
        truck_miles: int = 0,
        gas: int = 600,
        truck_id: int = 0,
        loaded_items: Union[list, str] = [],
    ) -> None:
        self.user_id = user_id
        self.name = name
        self.level = level
        self.xp = xp
        self.money = money
        if isinstance(position, str):
            # format the database string into a list
            self.position = [int(position[: position.find("/")]), int(position[position.find("/") + 1 :])]
        else:
            self.position = position
        self.miles = miles
        self.truck_miles = truck_miles
        self.gas = gas
        self.truck_id = truck_id
        if isinstance(position, str):
            # split the item string and get the items
            self.loaded_items: list = []
            if loaded_items != "":
                for item_name in loaded_items.split(";"):
                    self.loaded_items.append(items.get(item_name))
        else:
            self.loaded_items: list = loaded_items

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self.n]
            self.n += 1
            if attr == "position":
                return _format_pos_to_db(self.__getattribute__(attr))
            elif attr == "loaded_items":
                return _format_items_to_db(self.__getattribute__(attr))
            else:
                return self.__getattribute__(attr)
        else:
            raise StopIteration

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"

    async def add_xp(self, amount: int) -> str:
        """
        Add xp to the player and performs a level up if needed
        """
        answer = "\nYou got {:,} xp".format(amount)
        await update(self, xp=int(self.xp) + amount)
        while int(self.xp) >= levels.get_next_xp(self.level):
            await update(self, level=self.level + 1, xp=self.xp - levels.get_next_xp(self.level))
            answer += f"\n:tada: You leveled up to level {self.level} :tada:"
        return answer

    async def add_money(self, amount) -> None:
        """
        Add money to the players account
        """
        await update(self, money=self.money + amount)

    async def debit_money(self, amount) -> None:
        """
        Debit money from the players account
        """
        if amount > self.money:
            raise NotEnoughMoney()
        await update(self, money=self.money - amount)

    async def load_item(self, item: items.Item) -> None:
        """
        Add an item to the list of loaded items
        """
        new_items = self.loaded_items
        new_items.append(item)
        await update(self, loaded_items=new_items)

    async def unload_item(self, item: items.Item) -> None:
        """
        Remove an items from the list of loaded items
        """
        new_items = self.loaded_items
        items_to_remove = []
        for loaded_item in new_items:
            if loaded_item.name == item.name:
                items_to_remove.append(loaded_item)

        for loaded_item in items_to_remove:
            new_items.remove(loaded_item)

        await update(self, loaded_items=new_items)


async def insert(player: Player) -> None:
    """
    Inserts a player into the database
    """
    logging.info("Inserted %s into the database as %s", player.name, tuple(player))
    await __con__.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(player))
    await __con__.commit()


async def remove(player: Player) -> None:
    """
    Removes a player from the database
    """
    await __con__.execute("DELETE FROM players WHERE id=:id", {"id": player.user_id})
    await __con__.commit()
    logging.info("Removed %s %s from the database", player.name, tuple(player))


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
        await __con__.execute("UPDATE players SET position=? WHERE id=?", (_format_pos_to_db(position), player.user_id))
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
            "UPDATE players SET loaded_items=? WHERE id=?", (_format_items_to_db(loaded_items), player.user_id)
        )
        player.loaded_items = loaded_items
    await __con__.commit()
    logging.debug("Updated player %s to %s", player.name, tuple(player))


async def get(user_id: int) -> Player:
    """
    Get one player from the database
    """
    if not await registered(user_id):
        raise PlayerNotRegistered(user_id)
    cur = await __con__.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    player_tuple: tuple = await cur.fetchone()
    await cur.close()
    return Player(*player_tuple)


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
    top_players = []
    for tup in top_tuples:
        top_players.append(Player(*tup))
    return top_players, suffix


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
