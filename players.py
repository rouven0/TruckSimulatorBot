"""
This file contains the important player dataclasses
"""
from dataclasses import dataclass, field
import sqlite3

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

def remove(player :Player):
    """
    Removes a player from the database
    """
    __cur__.execute('DELETE FROM players WHERE id=:id', {"id": player.user_id})
    __con__.commit()

def update(player: Player, name=None, money=None, position=None, miles=None):
    """
    Updates a player in the database
    """
    if name is not None:
        __cur__.execute('UPDATE players SET name=? WHERE id=?', (name, player.user_id))
    if money is not None:
        __cur__.execute('UPDATE players SET money=? WHERE id=?', (money, player.user_id))
    if position is not None:
        __cur__.execute('UPDATE players SET position=? WHERE id=?',
                        (__format_pos_to_db(position), player.user_id))
    if miles is not None:
        __cur__.execute('UPDATE players SET miles=? WHERE id=?', (miles, player.user_id))
    __con__.commit()

def get(user_id):
    """
    Get one player from the database
    """
    __cur__.execute("SELECT * FROM players WHERE id=:id", {"id": user_id})
    try:
        return __from_tuple(__cur__.fetchone())
    except TypeError:
        return None

def get_top(key):
    """
    Get the top 10 players from the database
    """
    __cur__.execute("SELECT * FROM players ORDER BY key=:key DESC", {"key": key})
    return __list_from_tuples(__cur__.fetchmany(10))

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

class ActiveDrive():
    def __init__(self, player, message, last_action_time):
        self.player = player
        self.message = message
        self.last_action_time = last_action_time
        self.__locked = False

    def lock(self):
        self.__locked = True

    def unlock(self):
        self.__locked = False

    def islocked(self):
        return self.__locked
