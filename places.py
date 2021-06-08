"""
This module provides the Place class and several lists of places easy to access
"""
from dataclasses import dataclass
import sqlite3

def __get_position(db_pos):
    """
    Formats the position string from the database into a list what we can operate with
    """
    pos_x = db_pos[:db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/")+1:]
    return [int(pos_x), int(pos_y)]

def __generate_list(lst):
    """
    Populates a list with Place objects created from database tuples
    """
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
    """
    Attributes:
        name: The name of the place
        position: the Place's position in the 2 dimensional array that I call Map
        commands: all local available commands stored as strings in a list
        image_url: Every place has an image that is shown while driving
                   Images are hosted on a ressource discord server and displayed in embeds via URL
        produced_item: Items this place produces in jobs.
                       This is None when the place is not quest_active
    """
    name: str
    position: list
    commands: list
    image_url: str
    produced_item: str

def get(position):
    """
    Returns a place object on a specific position
    If no places is registered there, None is returned
    """
    if isinstance(position, str):
        position = __get_position(position)
    for place in get_all():
        if place.position == position:
            return place
    return Place("Nothing", position, [], None, None)

def get_all():
    """
    Returns all places that are currently loaded
    """
    return __all_places__

def get_public():
    """
    Returns places that should be shown in the addressbook
    """
    return __public_places__

def get_hidden():
    """
    Returns places that should NOT be shown in the addressbook
    """
    return __hidden_places__

def get_quest_active():
    """
    Returns all places that can appear in jobs
    """
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
