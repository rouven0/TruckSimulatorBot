"""
This module contains the Player class, several methods to operate with players in the database and
the DrivingPlayer, used to manage driving sessions
"""
from typing import Optional, Union
import logging
import api.database as database
import api.levels as levels
import api.items as items
from api.jobs import Job


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
        gas: amount of gas the player has
        truck_id: id of the player's truck
        loaded_items: a list of items the player has loaded
        company: the player's company
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
        company: str = None,
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
        self.company = company

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
        await database.con.execute("UPDATE players SET money=? WHERE id=?", (self.money + amount, self.user_id))
        self.money += amount

    async def debit_money(self, amount) -> None:
        """
        Debit money from the players account
        """
        if amount > self.money:
            raise NotEnoughMoney()
        await database.con.execute("UPDATE players SET money=? WHERE id=?", (self.money - amount, self.user_id))
        self.money -= amount

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

    async def add_job(self, job: Job) -> None:
        """
        Inserts a Job object into the players database
        """
        await database.con.execute("INSERT INTO jobs VALUES (?,?,?,?,?)", tuple(job))
        await database.con.commit()

    async def update_job(self, job: Job, state: int) -> None:
        """
        Updates a job's state
        """
        await database.con.execute("UPDATE jobs SET state=? WHERE player_id=?", (state, job.player_id))
        await database.con.commit()

    async def remove_job(self, job: Job) -> None:
        """
        Removes a job from the player database
        """
        await database.con.execute("DELETE FROM jobs WHERE player_id=:id", {"id": job.player_id})
        await database.con.commit()

    async def get_job(self) -> Optional[Job]:
        """
        Get the Players current job
        """
        cur = await database.con.execute("SELECT * FROM jobs WHERE player_id=:id", {"id": self.user_id})
        job_tuple = await cur.fetchall()
        if len(job_tuple) > 0:
            return Job(*(job_tuple[0]))
        else:
            return None

    async def remove_from_company(self):
        """
        Method I had to make to set a player's company to None
        """
        await database.con.execute("UPDATE players SET company=? WHERE id=?", (None, self.user_id))
        await database.con.commit()


async def insert(player: Player) -> None:
    """
    Inserts a player into the database
    """
    await database.con.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", tuple(player))
    await database.con.commit()
    logging.info("Inserted %s into the database as %s", player.name, tuple(player))


async def remove(player: Player) -> None:
    """
    Removes a player from the database
    """
    await database.con.execute("DELETE FROM players WHERE id=:id", {"id": player.user_id})
    await database.con.commit()
    logging.info("Removed %s %s from the database", player.name, tuple(player))


async def update(
    player: Player,
    name: str = None,
    level: int = None,
    xp: int = None,
    position: list = None,
    miles: int = None,
    truck_miles: int = None,
    gas: int = None,
    truck_id: int = None,
    loaded_items: list = None,
    company: str = None,
) -> None:
    """
    Updates a player in the database
    """
    if name is not None:
        await database.con.execute("UPDATE players SET name=? WHERE id=?", (name, player.user_id))
        player.name = name
    if level is not None:
        await database.con.execute("UPDATE players SET level=? WHERE id=?", (level, player.user_id))
        player.level = level
    if xp is not None:
        await database.con.execute("UPDATE players SET xp=? WHERE id=?", (xp, player.user_id))
        player.xp = xp
    if position is not None:
        await database.con.execute(
            "UPDATE players SET position=? WHERE id=?", (_format_pos_to_db(position), player.user_id)
        )
        player.position = position
    if miles is not None:
        await database.con.execute("UPDATE players SET miles=? WHERE id=?", (miles, player.user_id))
        player.miles = miles
    if truck_miles is not None:
        await database.con.execute("UPDATE players SET truck_miles=? WHERE id=?", (truck_miles, player.user_id))
        player.truck_miles = truck_miles
    if gas is not None:
        await database.con.execute("UPDATE players SET gas=? WHERE id=?", (gas, player.user_id))
        player.gas = gas
    if truck_id is not None:
        await database.con.execute("UPDATE players SET truck_id=? WHERE id=?", (truck_id, player.user_id))
        player.truck_id = truck_id
    if loaded_items is not None:
        await database.con.execute(
            "UPDATE players SET loaded_items=? WHERE id=?", (_format_items_to_db(loaded_items), player.user_id)
        )
        player.loaded_items = loaded_items
    if company is not None:
        await database.con.execute("UPDATE players SET company=? WHERE id=?", (company, player.user_id))
        player.company = company
    await database.con.commit()
    logging.debug("Updated player %s to %s", player.name, tuple(player))


async def get(user_id: int) -> Player:
    """
    Get one player from the database
    """
    if not await registered(user_id):
        raise PlayerNotRegistered(user_id)
    cur = await database.con.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    player_tuple: tuple = await cur.fetchone()
    await cur.close()
    player = Player(*player_tuple)
    if player.xp == -1:
        raise PlayerBlacklisted(player.user_id, player.name)
    return player


async def get_top(key) -> tuple:
    """
    Get the top 10 players from the database
    """
    if key == "money":
        cur = await database.con.execute("SELECT * FROM players ORDER BY money DESC")
        suffix = "$"
    elif key == "miles":
        cur = await database.con.execute("SELECT * FROM players ORDER BY miles DESC")
        suffix = " miles"
    else:
        cur = await database.con.execute("SELECT * FROM players ORDER BY level DESC, xp DESC")
        suffix = ""
    top_tuples = await cur.fetchmany(15)
    await cur.close()
    top_players = []
    for tup in top_tuples:
        top_players.append(Player(*tup))
    return top_players, suffix


async def registered(user_id: int) -> bool:
    """
    Checks whether a specific user is registered or not
    """
    cur = await database.con.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    if len(await cur.fetchall()) == 1:
        await cur.close()
        return True
    await cur.close()
    return False


async def get_count(table: str) -> int:
    """
    Returns the player count
    """
    # i know it's bad, but I have to do it
    cur = await database.con.execute(f"SELECT COUNT(*) FROM {table}")
    number_tuple = await cur.fetchall()
    await cur.close()
    return number_tuple[0][0]


class DrivingPlayer(Player):
    """
    Object to manage current driving session and prevent duplicate driving
    Attributes:
        message: Discord message where the drive is displayed and where the reactions are
        last_action_time: Time used to keep the list clean and time out drives
    """

    def __init__(self, *args, message_id=0, last_action_time=0) -> None:
        super().__init__(*args)
        self.message_id = message_id
        self.last_action_time = last_action_time

    async def start_drive(self) -> None:
        await database.con.execute(
            "INSERT INTO driving_players VALUES (?,?,?)", (self.user_id, self.message_id, self.last_action_time)
        )
        await database.con.commit()
        logging.info("%s started driving", self.name)

    async def stop_drive(self) -> None:
        await database.con.execute("DELETE FROM driving_players WHERE user_id=:id", {"id": self.user_id})
        await database.con.commit()
        logging.info("%s stopped driving", self.name)

    async def set_last_action_time(self, time) -> None:
        await database.con.execute(
            "UPDATE driving_players SET last_action_time=? WHERE user_id=?", (time, self.user_id)
        )
        await database.con.commit()


async def is_driving(user_id: int) -> bool:
    """
    Checks whether a specific user is driving
    """
    cur = await database.con.execute("SELECT * FROM driving_players WHERE user_id=:id", {"id": user_id})
    if len(await cur.fetchall()) == 1:
        await cur.close()
        return True
    await cur.close()
    return False


async def is_active_drive(user_id: int, message_id: int) -> bool:
    """
    Checks whether an interaction is done by a driving player
    """
    cur = await database.con.execute(
        "SELECT * FROM driving_players WHERE user_id=:user_id AND message_id=:message_id",
        {"user_id": user_id, "message_id": message_id},
    )
    if len(await cur.fetchall()) == 1:
        await cur.close()
        return True
    await cur.close()
    return False


async def get_driving_player(user_id: int, message_id: int = None) -> DrivingPlayer:
    if message_id is not None:
        if await is_active_drive(user_id, message_id):
            cur = await database.con.execute(
                "SELECT * FROM driving_players WHERE user_id=:user_id AND message_id=:message_id",
                {"user_id": user_id, "message_id": message_id},
            )
            data_tuple: tuple = await cur.fetchone()
            last_action_time = data_tuple[2]
            await cur.close()
            return DrivingPlayer(*tuple(await get(user_id)), message_id=message_id, last_action_time=last_action_time)
        else:
            raise NotDriving()
    else:
        # get drive by user id only
        cur = await database.con.execute("SELECT * FROM driving_players WHERE user_id=:user_id", {"user_id": user_id})
        data_tuple: tuple = await cur.fetchone()
        last_action_time = data_tuple[2]
        await cur.close()
        return DrivingPlayer(*tuple(await get(user_id)), message_id=message_id, last_action_time=last_action_time)


async def get_all_driving_players() -> list:
    cur = await database.con.execute("SELECT * from driving_players")
    driving_players = []
    for data_tuple in await cur.fetchall():
        driving_players.append(
            DrivingPlayer(*tuple(await get(data_tuple[0])), message_id=data_tuple[1], last_action_time=data_tuple[2])
        )
    await cur.close()
    return driving_players


class PlayerNotRegistered(Exception):
    """
    Exception raised when a player that is not registered is requested
    """

    def __init__(self, requested_id, *args: object) -> None:
        self.requested_id = requested_id
        super().__init__(*args)

    def __str__(self) -> str:
        return f"The requested player ({self.requested_id}) is not registered"


class PlayerBlacklisted(Exception):
    """
    Exception raised when a player is blacklisted
    """

    def __init__(self, requested_id, reason, *args: object) -> None:
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


class NotDriving(Exception):
    """
    Exception raised when a requested driving player is not driving
    """

    def __str__(self) -> str:
        return "The requested driving player isn't driving"
