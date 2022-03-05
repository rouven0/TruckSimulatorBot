"""
Items can be loaded and unloaded from the truck at all places. They mostly consist of a name and an emoji
"""
from dataclasses import dataclass
import sqlite3


@dataclass
class Item:
    """
    Represents an item that can be loaded

    :ivar str name: The name of the item
    :ivar str emoji: The item's emoji, shown on the map as place icon
    :ivar str description: The item's description, to be seen in the iteminfo
    """

    name: str
    emoji: int
    description: str

    def __str__(self) -> str:
        return f"<:placeholder:{self.emoji}> {self.name}"


def __generate_list(lst) -> None:
    for i in __cur__.fetchall():
        lst.append(Item(*i))


def get(name) -> Item:
    """
    Get an item by its name

    :param str name: The desired item's name
    :raises ItemNotFound: In case the item doesn't exist
    :return: The corresponding item
    """
    for item in __all_items__:
        if item.name == name:
            return item
    raise ItemNotFound()


def get_all() -> list:
    """
    :return: A list of all available items
    """
    return __all_items__


__con__ = sqlite3.connect("./resources/objects.db")
__cur__ = __con__.cursor()

__cur__.execute("SELECT * FROM items")
__all_items__ = []
__generate_list(__all_items__)

__con__.close()


class ItemNotFound(Exception):
    """Exception raised when requested item is not found"""

    def __str__(self) -> str:
        return "Requested item not found"
