"""
This module provides the Place class and several lists of places easy to access
"""
from dataclasses import dataclass
import sqlite3
from typing import Optional


@dataclass
class Place:
    """
    Attributes:
        name: The name of the place
        position: the Place's position in the 2 dimensional array that I call Map
        available_actions: all local available commands stored as strings in a list
        image_url: Every place has an image that is shown while driving
                   Images are hosted on a ressource discord server and displayed in embeds via URL
        image_url_better: image with the better truck
        image_url_tropical: image with the tropical truck
        image_url_ultimate: image with the ultimate truck
        produced_item: Item this place produces in jobs.
        accepted_item: Item this place rewards
        item_reward: money payed when the accepted_item is unloaded
    """

    name: str
    position: list
    available_actions: list
    image_url_default: Optional[str]
    image_url_jungle: Optional[str]
    image_url_tropical: Optional[str]
    image_url_hell: Optional[str]
    produced_item: Optional[str]
    accepted_item: Optional[str]
    item_reward: Optional[int]


def __get_position(db_pos) -> list:
    """
    Formats the position string from the database into a list what we can operate with
    """
    pos_x = db_pos[: db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/") + 1 :]
    return [int(pos_x), int(pos_y)]


def __generate_list(lst) -> None:
    """
    Populates a list with Place objects created from database tuples
    """
    for tup in __cur__.fetchall():
        name = tup[0]
        position = __get_position(tup[1])
        available_actions = []
        if tup[2] is not None:
            available_actions = tup[2].split(";")
        image_url = tup[3]
        image_url_better = tup[4]
        image_url_tropical = tup[5]
        image_url_ultimate = tup[6]
        produced_item = tup[7]
        accepted_item = tup[8]
        item_reward = tup[9]
        lst.append(
            Place(
                name,
                position,
                available_actions,
                image_url,
                image_url_better,
                image_url_tropical,
                image_url_ultimate,
                produced_item,
                accepted_item,
                item_reward,
            )
        )


def get(position) -> Place:
    """
    Returns a place object on a specific position
    If no places is registered there, None is returned
    """
    if isinstance(position, str):
        position = __get_position(position)
    for place in get_all():
        if place.position == position:
            return place
    return Place("Nothing", position, [], None, None, None, None, None, None, None)


def get_all() -> list:
    """
    Returns all places that are currently loaded
    """
    return __all_places__


def get_public() -> list:
    """
    Returns places that should be shown in the addressbook
    """
    return __public_places__


def get_hidden() -> list:
    """
    Returns places that should NOT be shown in the addressbook
    """
    return __hidden_places__


__con__ = sqlite3.connect("./resources/objects.db")
__cur__ = __con__.cursor()

__all_places__ = []
__cur__.execute("SELECT * FROM places")
__generate_list(__all_places__)

__public_places__ = []
__cur__.execute("SELECT * FROM places WHERE visibility=0")
__generate_list(__public_places__)

__hidden_places__ = []
__cur__.execute("SELECT * FROM places WHERE visibility=1")
__generate_list(__hidden_places__)

__con__.close()
