# pylint: disable=invalid-name,attribute-defined-outside-init
"""
This module contains the Player class, several methods to operate with players in the database and
the DrivingPlayer, used to manage driving sessions
"""
from dataclasses import field, dataclass
import inspect
from time import time
from typing import Optional, Any
import logging
from resources import database
from resources import levels
from resources import items
from resources.jobs import Job
from resources import position as pos


def _format_items_to_db(item_list: list) -> str:
    """
    Returns a database-ready string containing all the items
    :param list item_list: A list of items to format
    :return str: Database ready string
    """
    db_items = ""
    for item in item_list:
        db_items += item.name + ";"
    # remove the last ;
    return db_items[: len(db_items) - 1]


@dataclass
class Player:
    """
    A class representing a Player in the database

    :ivar str id: Unique discord user id to identify the player
    :ivar str name: Displayed name in discord, NOT the Nickname
    :ivar str discriminator: A user's discriminator. 4 digit number.
    :ivar int level: The player's level
    :ivar int xp: Xp for current level
    :ivar int money: Amount of in-game currency the player has
    :ivar position.Position position: Position on the 2 dimensional array that I call map
    :ivar int miles: Amount of miles the Player has driven
    :ivar int gas: Amount of gas the player has
    :ivar int truck_id: Id of the player's truck
    :ivar list loaded_items: A list of items the player has loaded
    :ivar int company: The name of the player's company
    :ivar int last_vote: The last vote as a unix timestamp
    """

    id: str
    name: str
    discriminator: str
    level: int = 0
    xp: int = 0
    money: int = 0
    position: pos.Position = pos.Position(0, 0)
    miles: int = 0
    truck_miles: int = 0
    gas: int = 0
    truck_id: int = 0
    loaded_items: list = field(default_factory=lambda: [])
    company: Optional[int] = None
    last_vote: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.position, int):
            self.position = pos.Position.from_int(self.position)
        if isinstance(self.loaded_items, str):
            # split the item string and get the items
            loaded_items: list = []
            if self.loaded_items != "":
                for item_name in self.loaded_items.split(";"):
                    loaded_items.append(items.get(item_name))
            self.loaded_items = loaded_items

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr == "position":
                return int(self.__getattribute__(attr))
            if attr == "loaded_items":
                return _format_items_to_db(self.__getattribute__(attr))
            return self.__getattribute__(attr)
        raise StopIteration

    def __str__(self) -> str:
        return f"**{self.name}**#{self.discriminator}"

    def __setattr__(self, __name: str, __value: Any) -> None:
        """
        Overrides the setattr method to update the database when a value is changed

        :param str __name: Name of the attribute
        :param Any __value: Value of the attribute
        """
        context = inspect.getouterframes(inspect.currentframe())[1][3]
        if context not in ["__init__", "__post_init__", "__next__", "__iter__"]:
            if __name == "position":
                __value_db = int(__value)
            elif __name == "loaded_items":
                __value_db = _format_items_to_db(__value)
            else:
                __value_db = __value
            table = "driving_players" if __name in ["last_action_time", "followup_url"] else "players"
            sql_base = f"UPDATE {table} SET {__name}=%s WHERE id=%s"
            database.cur.execute(sql_base, (__value_db, self.id))
            database.con.commit()
        super().__setattr__(__name, __value)

    def add_xp(self, amount: int) -> str:
        """
        Add xp to the player and performs a level up if needed

        :param int amount: Amount of xp that should be added
        :return: A string containing a message reflecting the xp increase, displayed in some embeds
        """
        answer = f"\nYou got {amount:,} xp"
        if round(time()) - self.last_vote < 1800:
            amount = amount * 2
        self.xp = int(self.xp) + amount
        while int(self.xp) >= levels.get_next_xp(self.level):
            self.xp -= levels.get_next_xp(self.level)
            self.level += 1
            answer += f"\n:tada: You leveled up to level {self.level} :tada:"
        return answer

    def add_money(self, amount) -> None:
        """
        Add money to the players account

        :param int amount: Amount of money that should be added
        """
        self.money += amount

    def debit_money(self, amount) -> None:
        """
        Debit money from the players account

        :param int amount: Amount of money that should be removed
        :raises NotEnoughMoney: In case the amount in too high
        """
        if amount > self.money:
            raise NotEnoughMoney()
        self.money -= amount

    def load_item(self, item: items.Item) -> None:
        """
        Add an item to the list of loaded items

        :param items.Item item: Item that should be added
        """
        new_items = self.loaded_items
        new_items.append(item)
        self.loaded_items = new_items

    def unload_item(self, item: items.Item) -> None:
        """
        Remove an items from the list of loaded items

        :param items.Item item: Item that should be removed
        """
        new_items = self.loaded_items
        items_to_remove = []
        for loaded_item in new_items:
            if loaded_item.name == item.name:
                items_to_remove.append(loaded_item)

        for loaded_item in items_to_remove:
            new_items.remove(loaded_item)
        self.loaded_items = new_items

    @staticmethod
    def add_job(job: Job) -> None:
        """
        Inserts a Job object into the players database

        :param jobs.Job job: Job that should be inserted
        """
        placeholders = ", ".join(["%s"] * len(vars(job)))
        columns = ", ".join(vars(job).keys())
        sql = f"INSERT INTO jobs({columns}) VALUES ({placeholders})"
        database.cur.execute(sql, tuple(job))
        database.con.commit()

    @staticmethod
    def update_job(job: Job, state: int) -> None:
        """
        Updates a job's state

        :param jobs.Job job: The Job that should be updated
        :param int state: The new state of the job
        """
        database.cur.execute("UPDATE jobs SET state=%s WHERE player_id=%s", (state, job.player_id))
        database.con.commit()

    @staticmethod
    def remove_job(job: Job) -> None:
        """
        Removes a job from the player database

        :param jobs.Job job: The Job that should be removed
        """
        database.cur.execute("DELETE FROM jobs WHERE player_id=%s", (job.player_id,))
        database.con.commit()

    def get_job(self) -> Optional[Job]:
        """
        Get the Players current job

        :return: A job if the player currently has a running job
        """
        database.cur.execute("SELECT * FROM jobs WHERE player_id=%s", (self.id,))
        records = database.cur.fetchall()
        if len(records) > 0:
            return Job(**records[0])
        return None


def insert(player: Player) -> None:
    """
    Inserts a player into the database

    :param Player player: Player that should be inserted
    """
    placeholders = ", ".join(["%s"] * len(vars(player)))
    columns = ", ".join(vars(player).keys())
    sql = f"INSERT INTO players({columns}) VALUES ({placeholders})"
    database.cur.execute(sql, tuple(player))
    database.con.commit()
    logging.info("Inserted %s into the database as %s", player.name, tuple(player))


def get(id: str, check: str = None) -> Player:
    """
    Get one player from the database

    :param str id: The requested player's id
    :param str check: When given, this method will compare id and check, this is used to verify component "owners"
    :return: The corresponding player
    :raises PlayerNotRegistered: in case a player is not found in the database
    :raises PlayerBlacklisted: in case a player is on the blacklist
    """
    if not registered(id):
        raise PlayerNotRegistered(id)
    if check and id != check:
        raise WrongPlayer()
    database.cur.execute("SELECT * FROM players WHERE id=%s", (id,))
    record = database.cur.fetchone()
    player = Player(**record)
    if player.xp == -1:
        raise PlayerBlacklisted(player.id, player.name)
    return player


def get_top(key: str) -> tuple:
    """
    Get the top 10 players from the database

    :param str key: Key to sort the player list by
    :return:
        - :top_players: A list of the top players
        - :suffix: A suffix to be shown in the list
    """
    if key == "money":
        database.cur.execute("SELECT * FROM players ORDER BY money DESC")
        suffix = "$"
    elif key == "miles":
        database.cur.execute("SELECT * FROM players ORDER BY miles DESC")
        suffix = " miles"
    else:
        database.cur.execute("SELECT * FROM players ORDER BY level DESC, xp DESC")
        suffix = ""
    top_records = database.cur.fetchmany(15)
    # clean the cursor to prevent errors
    database.cur.fetchall()
    top_players = []
    for record in top_records:
        top_players.append(Player(**record))
    return top_players, suffix


def registered(id: str) -> bool:
    """
    Checks whether a specific user is registered or not

    :param int id: User id to check
    :return: A boolean indicating the registered state
    """
    database.cur.execute("SELECT * FROM players WHERE id=%s", (id,))
    if len(database.cur.fetchall()) == 1:
        return True
    return False


def get_count(table: str) -> int:
    """
    Returns a table's  rowcount

    :param str table: Table to look at
    :return: The row count of the table
    """
    # update the connection in case of the timeout-thread doing something
    database.con.commit()
    database.cur.execute("SELECT COUNT(*) FROM " + table)
    record = database.cur.fetchone()
    return record["COUNT(*)"]


class DrivingPlayer(Player):
    """
    Object to manage current driving session and prevent duplicate driving

    :ivar str followup_url: Url granting access to the drive message
    :ivar int last_action_time: Time used to keep the list clean and time out drives
    """

    def __init__(self, followup_url="", last_action_time=0, **kwargs) -> None:
        self.followup_url = followup_url
        self.last_action_time = last_action_time
        super().__init__(**kwargs)

    def start_drive(self) -> None:
        """Inserts a driving player into the database"""
        database.cur.execute(
            "INSERT INTO driving_players(id, followup_url, last_action_time) VALUES (%s,%s,%s)",
            (self.id, self.followup_url, self.last_action_time),
        )
        database.con.commit()
        logging.info("%s started driving", self.name)

    def stop_drive(self) -> None:
        """Removes a driving player from the database"""
        database.cur.execute("DELETE FROM driving_players WHERE id=%s", (self.id,))
        database.con.commit()
        logging.info("%s stopped driving", self.name)


def is_driving(id: str) -> bool:
    """
    Checks whether a specific user is driving

    :param int id: The id to check
    :return: A boolean indicating whether user is driving
    """
    # update the connection in case of the timeout-thread doing something
    database.con.commit()
    database.cur.execute("SELECT * FROM driving_players WHERE id=%s", (id,))
    if len(database.cur.fetchall()) == 1:
        return True
    return False


def get_driving_player(id: str, check: str = None) -> DrivingPlayer:
    """
    Get a driving player from the database

    :param str id: The id to search for
    :param str check: When given, this method will compare id and check, this is used to verify component "owners"
    :raises NotDriving: When id and check mismatch
    :return: The corresponding driving player
    """
    if check and id != check:
        raise WrongPlayer()
    if is_driving(id):
        database.cur.execute("SELECT * FROM driving_players WHERE id=%s", (id,))
        record = database.cur.fetchone()
        followup_url = record["followup_url"]
        last_action_time = record["last_action_time"]
        return DrivingPlayer(**vars(get(id)), followup_url=followup_url, last_action_time=last_action_time)
    raise WrongPlayer()


def get_all_driving_players() -> list[DrivingPlayer]:
    """
    Get all driving players from the database

    :return: A list of all driving players
    """
    # update the connection in case of the timeout-thread doing something
    database.con.commit()
    database.cur.execute("SELECT * from driving_players")
    driving_players = []
    for record in database.cur.fetchall():
        driving_players.append(
            DrivingPlayer(
                **vars(get(record["id"])),
                followup_url=record["followup_url"],
                last_action_time=record["last_action_time"],
            )
        )
    return driving_players


class PlayerNotRegistered(Exception):
    """
    Exception raised when a player that is not registered is requested

    :ivar str requested_id: Id of the requested player
    """

    def __init__(self, requested_id: str, *args: object) -> None:
        self.requested_id = requested_id
        super().__init__(*args)

    def __str__(self) -> str:
        return f"The requested player ({self.requested_id}) is not registered"


class PlayerBlacklisted(Exception):
    """
    Exception raised when a player is blacklisted

    :ivar str requested_id: Id of the blacklisted player
    :ivar str reason: Reason of the ban
    """

    def __init__(self, requested_id: str, reason: str, *args: object) -> None:
        self.requested_id = requested_id
        self.reason = reason
        super().__init__(*args)

    def __str__(self) -> str:
        return f"The requested player ({self.requested_id}) is blacklisted for reason {self.reason}"


class NotEnoughMoney(Exception):
    """
    Exception raised when more money is withdrawn than the player has
    """

    def __str__(self) -> str:
        return "The requested player doesn't have enough money to perform this action"


class WrongPlayer(Exception):
    """
    Exception raised when a requested driving player is not driving
    """

    def __str__(self) -> str:
        return "The requested driving player isn't driving"
