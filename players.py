"""
This file contains the important player dataclasses
"""
from dataclasses import dataclass

def list_from_tuples(tups):
    """
    Returns a list with all Players generated from a set of tuples from the database
    """
    players = []
    for tup in tups:
        players.append(from_tuple(tup))
    return players

def from_tuple(tup):
    """
    Returns a Player object from a received database tuple
    """
    return Player(tup[0], tup[1], tup[2], get_position(tup[3]), tup[4])

def to_tuple(player):
    """
    Transforms the player object into a tuple that can be inserted in the db
    """
    return (player.user_id, player.name, player.money,
            format_pos_to_db(player.position), player.miles)

def get_position(db_pos):
    """
    Parses the position from the database as list [x][y]
    """
    pos_x = db_pos[:db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/")+1:]
    return [int(pos_x), int(pos_y)]

def format_pos_to_db(pos):
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])

@dataclass
class Player():
    user_id: int
    name: str
    money: float
    position: list
    miles: int

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
