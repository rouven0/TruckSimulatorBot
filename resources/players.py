# pylint: disable=invalid-name,no-self-use,attribute-defined-outside-init
"""
This module contains the Player class, several methods to operate with players in the database and
the DrivingPlayer, used to manage driving sessions
"""
from typing import Optional
import logging
from resources import database
from resources import levels
from resources import items
from resources.jobs import Job


def _format_pos_to_db(pos: list) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return f"{pos[0]}/{pos[1]}"


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
    ----------
        id: Unique discord user id to identify the player
        name: Displayed name in discord, NOT the Nickname
        level: players level
        xp: xp for current level
        money: Amount of in-game currency the player has
        position: Position on the 2 dimensional array that I call map
        miles: Amount of miles the Player has driven
        gas: amount of gas the player has
        truck_id: id of the player's truck
        loaded_items: a list of items the player has loaded
        company: the player's company
    """

    def __init__(self, id, name, **kwargs) -> None:
        self.id = id
        self.name = name
        self.level = kwargs.pop("level", 0)
        self.xp = kwargs.pop("xp", 0)
        self.money = kwargs.pop("money", 0)
        position = kwargs.pop("position", [0, 0])
        if isinstance(position, str):
            # format the database string into a list
            self.position = [int(position[: position.find("/")]), int(position[position.find("/") + 1 :])]
        else:
            self.position = position
        self.miles = kwargs.pop("miles", 0)
        self.truck_miles = kwargs.pop("truck_miles", 0)
        self.gas = kwargs.pop("gas", 0)
        self.truck_id = kwargs.pop("truck_id", 0)
        loaded_items = kwargs.pop("loaded_items", [])
        if isinstance(position, str):
            # split the item string and get the items
            self.loaded_items: list = []
            if loaded_items != "":
                for item_name in loaded_items.split(";"):
                    self.loaded_items.append(items.get(item_name))
        else:
            self.loaded_items: list = loaded_items
        self.company = kwargs.pop("company", None)

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr == "position":
                return _format_pos_to_db(self.__getattribute__(attr))
            if attr == "loaded_items":
                return _format_items_to_db(self.__getattribute__(attr))
            return self.__getattribute__(attr)
        raise StopIteration

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def add_xp(self, amount: int) -> str:
        """
        Add xp to the player and performs a level up if needed
        """
        answer = f"\nYou got {amount:,} xp"
        update(self, xp=int(self.xp) + amount)
        while int(self.xp) >= levels.get_next_xp(self.level):
            update(self, level=self.level + 1, xp=self.xp - levels.get_next_xp(self.level))
            answer += f"\n:tada: You leveled up to level {self.level} :tada:"
        return answer

    def add_money(self, amount) -> None:
        """
        Add money to the players account
        """
        database.cur.execute("UPDATE players SET money=%s WHERE id=%s", (self.money + amount, self.id))
        database.con.commit()
        self.money += amount

    def debit_money(self, amount) -> None:
        """
        Debit money from the players account
        """
        if amount > self.money:
            raise NotEnoughMoney()
        database.cur.execute("UPDATE players SET money=%s WHERE id=%s", (self.money - amount, self.id))
        database.con.commit()
        self.money -= amount

    def load_item(self, item: items.Item) -> None:
        """
        Add an item to the list of loaded items
        """
        new_items = self.loaded_items
        new_items.append(item)
        update(self, loaded_items=new_items)

    def unload_item(self, item: items.Item) -> None:
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

        update(self, loaded_items=new_items)

    def add_job(self, job: Job) -> None:
        """
        Inserts a Job object into the players database
        """
        placeholders = ", ".join(["%s"] * len(vars(job)))
        columns = ", ".join(vars(job).keys())
        sql = f"INSERT INTO jobs({columns}) VALUES ({placeholders})"
        print(sql)
        database.cur.execute(sql, tuple(job))
        database.con.commit()

    def update_job(self, job: Job, state: int) -> None:
        """
        Updates a job's state
        """
        database.cur.execute("UPDATE jobs SET state=%s WHERE player_id=%s", (state, job.player_id))
        database.con.commit()

    def remove_job(self, job: Job) -> None:
        """
        Removes a job from the player database
        """
        database.cur.execute("DELETE FROM jobs WHERE player_id=%s", (job.player_id,))
        database.con.commit()

    def get_job(self) -> Optional[Job]:
        """
        Get the Players current job
        """
        database.cur.execute("SELECT * FROM jobs WHERE player_id=%s", (self.id,))
        records = database.cur.fetchall()
        if len(records) > 0:
            return Job(**records[0])
        return None

    def remove_from_company(self):
        """
        Method I had to make to set a player's company to None
        """
        database.cur.execute("UPDATE players SET company=%s WHERE id=%s", (None, self.id))
        database.con.commit()


def insert(player: Player) -> None:
    """
    Inserts a player into the database
    """
    placeholders = ", ".join(["%s"] * len(vars(player)))
    columns = ", ".join(vars(player).keys())
    sql = f"INSERT INTO players({columns}) VALUES ({placeholders})"
    database.cur.execute(sql, tuple(player))
    database.con.commit()
    logging.info("Inserted %s into the database as %s", player.name, tuple(player))


def update(
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
        database.cur.execute("UPDATE players SET name=%s WHERE id=%s", (name, player.id))
        player.name = name
    if level is not None:
        database.cur.execute("UPDATE players SET level=%s WHERE id=%s", (level, player.id))
        player.level = level
    if xp is not None:
        database.cur.execute("UPDATE players SET xp=%s WHERE id=%s", (xp, player.id))
        player.xp = xp
    if position is not None:
        database.cur.execute("UPDATE players SET position=%s WHERE id=%s", (_format_pos_to_db(position), player.id))
        player.position = position
    if miles is not None:
        database.cur.execute("UPDATE players SET miles=%s WHERE id=%s", (miles, player.id))
        player.miles = miles
    if truck_miles is not None:
        database.cur.execute("UPDATE players SET truck_miles=%s WHERE id=%s", (truck_miles, player.id))
        player.truck_miles = truck_miles
    if gas is not None:
        database.cur.execute("UPDATE players SET gas=%s WHERE id=%s", (gas, player.id))
        player.gas = gas
    if truck_id is not None:
        database.cur.execute("UPDATE players SET truck_id=%s WHERE id=%s", (truck_id, player.id))
        player.truck_id = truck_id
    if loaded_items is not None:
        database.cur.execute(
            "UPDATE players SET loaded_items=%s WHERE id=%s", (_format_items_to_db(loaded_items), player.id)
        )
        player.loaded_items = loaded_items
    if company is not None:
        database.cur.execute("UPDATE players SET company=%s WHERE id=%s", (company, player.id))
        player.company = company
    database.con.commit()
    logging.debug("Updated player %s to %s", player.name, tuple(player))


def get(id: int) -> Player:
    """
    Get one player from the database
    """
    id = int(id)
    if not registered(id):
        raise PlayerNotRegistered(id)
    database.cur.execute("SELECT * FROM players WHERE id=%s", (id,))
    record = database.cur.fetchone()
    player = Player(**record)
    if player.xp == -1:
        raise PlayerBlacklisted(player.id, player.name)
    return player


def get_top(key) -> tuple:
    """
    Get the top 10 players from the database
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


def registered(id: int) -> bool:
    """
    Checks whether a specific user is registered or not
    """
    database.cur.execute("SELECT * FROM players WHERE id=%s", (id,))
    if len(database.cur.fetchall()) == 1:
        return True
    return False


def get_count(table: str) -> int:
    """
    Returns the player count
    """
    # update the connection in case of the timeout-thread doing something
    database.con.commit()
    database.cur.execute("SELECT COUNT(*) FROM " + table)
    record = database.cur.fetchone()
    return record["COUNT(*)"]


class DrivingPlayer(Player):
    """
    Object to manage current driving session and prevent duplicate driving
    Attributes:
        message: Discord message where the drive is displayed and where the reactions are
        last_action_time: Time used to keep the list clean and time out drives
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

    def update(self, time, followup_url) -> None:
        """
        Update the player on every interaction
        """
        database.cur.execute("UPDATE driving_players SET last_action_time=%s WHERE id=%s", (time, self.id))
        database.cur.execute("UPDATE driving_players SET followup_url=%s WHERE id=%s", (followup_url, self.id))
        database.con.commit()


def is_driving(id: int) -> bool:
    """
    Checks whether a specific user is driving
    """
    # update the connection in case of the timeout-thread doing something
    database.con.commit()
    database.cur.execute("SELECT * FROM driving_players WHERE id=%s", (id,))
    if len(database.cur.fetchall()) == 1:
        return True
    return False


def get_driving_player(id: int, check: int = None) -> DrivingPlayer:
    """
    Get a driving player from the database
    """
    id = int(id)
    if check and id != check:
        raise NotDriving()
    if is_driving(id):
        database.cur.execute("SELECT * FROM driving_players WHERE id=%s", (id,))
        record = database.cur.fetchone()
        followup_url = record["followup_url"]
        last_action_time = record["last_action_time"]
        return DrivingPlayer(**vars(get(id)), followup_url=followup_url, last_action_time=last_action_time)
    raise NotDriving()


def get_all_driving_players() -> list[DrivingPlayer]:
    """Get all driving players from the database"""
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
