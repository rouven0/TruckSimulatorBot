from dataclasses import dataclass
import sqlite3

def __get_position(db_pos):
    pos_x = db_pos[:db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/")+1:]
    return [int(pos_x), int(pos_y)]

def __generate_list(lst):
    for tup in __cur__.fetchall():
        name = tup[0]
        position = __get_position(tup[1])
        commands = []
        if tup[2] is not None:
            commands = tup[2].split(";")
        image_url = tup[3]
        produced_item = tup[5]
        lst.append(Place(name, position, commands, image_url, produced_item))

@dataclass
class Place():
    name: str
    position: list
    commands: list
    image_url: str
    produced_item: str

def get(position):
    if isinstance(position, str):
        position = __get_position(position)
    for place in get_all():
        if place.position == position:
            return place
    return None

def get_all():
    return __all_places__

def get_public():
    return __public_places__

def get_hidden():
    return __hidden_places__

def get_quest_active():
    return __quest_active_places__

__con__ = sqlite3.connect('objects.db')
__cur__ = __con__.cursor()

__all_places__ = []
__cur__.execute('SELECT * FROM places')
__generate_list(__all_places__)

__public_places__ = []
__cur__.execute('SELECT * FROM places WHERE visibility=0')
__generate_list(__public_places__)

__hidden_places__ = []
__cur__.execute('SELECT * FROM places WHERE visibility=1')
__generate_list(__hidden_places__)

__quest_active_places__ = []
__cur__.execute('SELECT * FROM places WHERE quest_active=1')
__generate_list(__quest_active_places__)

__con__.close()
