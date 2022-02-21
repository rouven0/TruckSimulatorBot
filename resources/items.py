"""
This module provides the item class and a list of items, easy to access with get()
"""
from dataclasses import dataclass
import sqlite3


@dataclass
class Item:
    """Represents an item that can be loaded"""

    name: str
    emoji: int
    description: str

    def __str__(self) -> str:
        return f"<:placeholder:{self.emoji}> {self.name}"


def __generate_list(lst) -> None:
    for i in __cur__.fetchall():
        lst.append(Item(*i))


def get(name) -> Item:
    """Get an item by its name"""
    for item in __all_items__:
        if item.name == name:
            return item
    raise ItemNotFound()


def get_all() -> list:
    """Get all items"""
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
