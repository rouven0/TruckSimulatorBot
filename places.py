from dataclasses import dataclass
import sqlite3

def __get_position(db_pos):
    pos_x = db_pos[db_pos.find("/")+1:]
    pos_y = db_pos[:db_pos.find("/")]
    return [int(pos_x), int(pos_y)]

def __generate_list(l):
    for p in cur.fetchall():
        name = p[0]
        position = __get_position(p[1])
        commands = []
        if p[2] is not None:
            commands = p[2].split(";")
        image_url = p[3]
        l.append(Place(name, position, commands, image_url))

@dataclass
class Place():
    name: str
    position: list
    commands: list
    image_url: str

def get(position):
    for place in get_all():
        if place.position == position:
            return place
    return None

def get_all():
    return __all_places

def get_public():
    return __public_places

def get_hidden():
    return __hidden_places

con = sqlite3.connect('objects.db')
cur = con.cursor()

__all_places = []
cur.execute('SELECT * FROM places WHERE visibility=0')
__generate_list(__all_places)

__public_places = []
cur.execute('SELECT * FROM places WHERE visibility=0')
__generate_list(__public_places)

__hidden_places = []
cur.execute('SELECT * FROM places WHERE visibility=1')
__generate_list(__hidden_places)

con.close()
