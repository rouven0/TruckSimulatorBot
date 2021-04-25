from dataclasses import dataclass

def list_from_tuples(tups):
    players = []
    for entry in tups:
        players.append(Player(entry[0], entry[1], entry[2], entry[3], get_position(entry[4])))
    return players

def from_tuple(tup):
    return Player(tup[0], tup[1], tup[2], tup[3], get_position(tup[4]))

def to_tuple(player):
    return (player.user_id, player.name, player.truck_id, player.money, format_pos_to_db(player.position))

def get_position(db_pos):
    pos_x = db_pos[db_pos.find("/")+1:]
    pos_y = db_pos[:db_pos.find("/")]
    return [int(pos_x), int(pos_y)]

def format_pos_to_db(pos):
    return "{}/{}".format(pos[0], pos[1])

@dataclass
class Player():
    user_id: int
    name: str
    truck_id: int
    money: float
    position: list

class DrivingPlayer():
    def __init__(self, player, message):
        self.player = player
        self.message = message
