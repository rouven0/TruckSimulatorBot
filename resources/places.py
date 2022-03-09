"""
Places are spread all over the map. They accept and produce certain items, used in jobs and minijobs
"""
from dataclasses import dataclass
import sqlite3
from typing import Optional, Union


@dataclass
class Place:
    """
    :ivar str name: The name of the place
    :ivar list position: the Place's position in the 2 dimensional array that I call Map
    :ivar list available_actions: all local available commands stored as strings in a list
    :ivar str image_url: Every place has an image that is shown while driving.
        Images are hosted on a resource discord server and displayed in embeds via URL
    :ivar str image_url_better: image with the better truck
    :ivar str image_url_tropical: image with the tropical truck
    :ivar str image_url_ultimate: image with the ultimate truck
    :ivar str produced_item: Item this place produces in jobs.
    :ivar str accepted_item: Item this place rewards
    :ivar int item_reward: money paid when the accepted_item is unloaded
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

    def __str__(self) -> str:
        return self.name


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


def get(position: Union[list, str]) -> Place:
    """
    Returns a place object on a specific position
    If no places is registered there, None is returned

    :param list/str position: Postion of the place
    :return: The corresponding place
    """
    if isinstance(position, str):
        position = __get_position(position)
    for place in get_all():
        if place.position == position:
            return place
    return Place("Nothing", position, [], None, None, None, None, None, None, None)


def get_matching_options(name: str) -> list[dict]:
    """
    Returns autocomplete choices for the placeinfo command

    :param str name: Partial name of the place
    :return: A list of choice dicts with all the matching place names and positions
    """
    return [
        {"name": place.name, "value": f"{place.position[0]}/{place.position[1]}"}
        for place in __all_places__
        if str.lower(name) in str.lower(place.name)
    ]


def get_all() -> list:
    """
    :return: All places in a list
    """
    return __all_places__


__con__ = sqlite3.connect("./resources/objects.db")
__cur__ = __con__.cursor()

__all_places__ = []
__cur__.execute("SELECT * FROM places")
__generate_list(__all_places__)
