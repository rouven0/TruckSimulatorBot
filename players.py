"""
This module contains the Player class, several methods to operate with players in the database and
the ActiveDrive, used to manage driving sessions
"""
from dataclasses import dataclass, field
import sqlite3
import logging
import discord

__con__ = sqlite3.connect('players.db')
__cur__ = __con__.cursor()

def __list_from_tuples(tups):
    """
    Returns a list with all Players generated from a set of tuples from the database
    """
    players = []
    for tup in tups:
        players.append(__from_tuple(tup))
    return players

def __from_tuple(tup):
    """
    Returns a Player object from a received database tuple
    """
    return Player(tup[0], tup[1], tup[2], __get_position(tup[3]), tup[4])

def __to_tuple(player):
    """
    Transforms the player object into a tuple that can be inserted in the db
    """
    return (player.user_id, player.name, player.money,
            __format_pos_to_db(player.position), player.miles)

def __get_position(db_pos):
    """
    Parses the position from the database as list [x][y]
    """
    pos_x = db_pos[:db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/")+1:]
    return [int(pos_x), int(pos_y)]

def __format_pos_to_db(pos):
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])

@dataclass
class Player():
    """
    Attributes:
        user_id: Unique discord user id to identify the player
        name: Displayed name in discord, NOT the Nickname
        money: Amount of ingame currency the player has
        position: Position on the 2 dimensional array that I call map
        miles: Amount of miles the Player has driven
    """
    user_id: int
    name: str
    money: float = 0
    position: list = field(default_factory=lambda: [0, 0])
    miles: int = 0

def insert(player: Player):
    """
    Inserts a player into the database
    """
    __cur__.execute('INSERT INTO players VALUES (?,?,?,?,?)', __to_tuple(player))
    __con__.commit()
    logging.info('Inserted %s into the database as %s', player.name, __to_tuple(player))

def remove(player :Player):
    """
    Removes a player from the database
    """
    __cur__.execute('DELETE FROM players WHERE id=:id', {"id": player.user_id})
    __con__.commit()
    logging.info('Removed %s from the database', player.name)

def update(player: Player, name=None, money=None, position=None, miles=None):
    """
    Updates a player in the database
    """
    if name is not None:
        __cur__.execute('UPDATE players SET name=? WHERE id=?', (name, player.user_id))
        player.name = name
    if money is not None:
        __cur__.execute('UPDATE players SET money=? WHERE id=?', (money, player.user_id))
        player.money = money
    if position is not None:
        __cur__.execute('UPDATE players SET position=? WHERE id=?',
                        (__format_pos_to_db(position), player.user_id))
        player.position = position
    if miles is not None:
        __cur__.execute('UPDATE players SET miles=? WHERE id=?', (miles, player.user_id))
        player.miles = miles
    __con__.commit()
    logging.info('Updated player %s to %s', player.name, __to_tuple(player))

def get(user_id):
    """
    Get one player from the database
    """
    __cur__.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    try:
        return __from_tuple(__cur__.fetchone())
    except TypeError:
        return None

def get_top(key="miles"):
    """
    Get the top 10 players from the database
    """
    if key == "money":
        __cur__.execute("SELECT * FROM players ORDER BY money DESC")
        suffix = "$"
    else:
        __cur__.execute("SELECT * FROM players ORDER BY miles DESC")
        suffix = " miles"
    return (__list_from_tuples(__cur__.fetchmany(10)), key, suffix)

def registered(user_id):
    """
    Checks whether a specific user is registered or not
    """
    __cur__.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    if len(__cur__.fetchall()) == 1:
        return True
    return False

def get_count():
    """
    Returns the player count
    """
    __cur__.execute("SELECT COUNT(*) FROM players")
    return __cur__.fetchall()[0][0]

@dataclass
class ActiveDrive():
    """
    Object to manage current driving session and prevent duplicate driving
    Attributes:
        player: Player object of the driving player
        message: Discord message where the drive is displayed and where the reacions are
        last_action_time: Time used to keep the list clean and time out drives
    """
    player: Player
    message: discord.Message
    last_action_time: float
