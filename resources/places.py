"""
Places are spread all over the map. They accept and produce certain items, used in jobs and minijobs
"""
from dataclasses import dataclass
import sqlite3
from typing import Optional, Union

from resources import symbols
from resources import position as pos


@dataclass
class Place:
    """
    :ivar str name: The name of the place
    :ivar position.Postion position: the Place's position as int
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
    position: pos.Position
    available_actions: list
    image_url_default: Optional[str]
    image_url_jungle: Optional[str]
    image_url_tropical: Optional[str]
    image_url_hell: Optional[str]
    produced_item: Optional[str]
    accepted_item: Optional[str]
    item_reward: Optional[int]

    def __post_init__(self) -> None:
        if isinstance(self.position, int):
            self.position = pos.Position.from_int(self.position)
        if isinstance(self.available_actions, str):
            self.available_actions = self.available_actions.split(";")

    def __str__(self) -> str:
        return self.name


def get_direction(player, target: Place) -> int:
    """
    A step based path finder
    :param players.Player player: Player to start with
    :param Place target: The place to navigate to
    :return: The emoji id of the direction. Used in buttons and the drive embed
    """
    if int(player.position) == int(target.position):
        return symbols.SUCCESS
    possible_directions = {}
    possible_directions["x"] = symbols.RIGHT if player.position.x < target.position.x else symbols.LEFT
    possible_directions["y"] = symbols.UP if player.position.y < target.position.y else symbols.DOWN
    return (
        possible_directions["x"]
        if abs(player.position.x - target.position.x) >= abs(player.position.y - target.position.y)
        else possible_directions["y"]
    )


def get(position: Union[int, pos.Position]) -> Place:
    """
    Returns a place object on a specific position
    If no places is registered there, None is returned

    :param list/str position: Postion of the place
    :return: The corresponding place
    """
    for place in get_all():
        if int(place.position) == int(position):
            return place
    # fix this
    return None


def get_all() -> list:
    """
    :return: All places in a list
    """
    return __all_places__


__con__ = sqlite3.connect("./resources/objects.db")
__cur__ = __con__.cursor()

__all_places__ = []
__cur__.execute("SELECT * FROM places")
for tup in __cur__.fetchall():
    __all_places__.append(Place(*tup))


class PlaceNotFound(Exception):
    """Exception raised when requested place is not found"""

    def __str__(self) -> str:
        return "Requested place not found"
