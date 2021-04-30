from dataclasses import dataclass
import sqlite3

def __get_position(db_pos):
    pos_x = db_pos[db_pos.find("/")+1:]
    pos_y = db_pos[:db_pos.find("/")]
    return [int(pos_x), int(pos_y)]

@dataclass
class Place():
    name: str
    position: list
    commands: list
    image_path: str

def get(position):
    for place in ALL:
        if place.position == position:
            return place     
    return None

def get_all():
    return ALL

con = sqlite3.connect('places.db')
cur = con.cursor()
cur.execute('SELECT * FROM places')

ALL = []
for p in cur.fetchall():
    name= p[0]
    position = __get_position(p[1])
    commands= []
    if p[2] is not None:
        commands = p[2].split(";")
    image_path=p[3]
    ALL.append(Place(name, position, commands, image_path))
con.close()
