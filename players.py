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
    return Player(tup[0], tup[1], tup[2], tup[3], get_position(tup[4]), tup[5].split(";"), get_position(tup[6]), get_position(tup[7]), tup[8])

def to_tuple(player):
    """
    Transforms the player object into a tuple that can be inserted in the db
    """
    return (player.user_id, player.name, player.truck_id, player.money, format_pos_to_db(player.position), format_items_to_db(player.quest_items), format_pos_to_db(player.quest_from), format_pos_to_db(player.quest_to), player.miles)

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

def format_items_to_db(items):
    """
    Returns a string in the form 'item0;item1;item2...' that is inserted into the database
    """
    res=""
    for item in items():
        if res == "":
            res=item
        else:
            res= res+";"+item

@dataclass
class Player():
    user_id: int
    name: str
    truck_id: int
    money: float
    position: list
    quest_items: list
    quest_from: list
    quest_to: list
    miles: int

class ActiveDrive():
    """
    The ActiveDrive object is used to identify and manage a set of user and message, that belong to a driving
    """
    def __init__(self, player, message, last_action_time):
        self.player = player
        self.message = message
        self.last_action_time = last_action_time
        self.islocked = False
