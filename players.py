from dataclasses import dataclass

def list_from_tuples(l):
    players = []
    for entry in l:
        players.append(Player(entry[0], entry[1], entry[2], entry[3], entry[4])) 
    return players
    
def from_tuple(t):
    return Player(t[0], t[1], t[2], t[3], t[4])

def to_tuple(p):
    return (p.user_id, p.name, p.truck_id, p.money, p.quest_id)

@dataclass
class Player():
    user_id:int
    name:str
    truck_id:int
    money:float
    quest_id:int    
