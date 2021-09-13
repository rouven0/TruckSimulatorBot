"""
This module provides the item class and a list of items, easy to access with get()
"""
from dataclasses import dataclass
import sqlite3


@dataclass
class Item:
    name: str
    emoji: int
    description: str


def __generate_list(lst) -> None:
    for i in __cur__.fetchall():
        lst.append(Item(i[0], int(i[1]), i[2]))


def get(name) -> Item:
    for item in __all_items__:
        if item.name == name:
            return item
    raise ItemNotFound()


def get_all() -> list:
    return __all_items__


__con__ = sqlite3.connect("./api/objects.db")
__cur__ = __con__.cursor()

__cur__.execute("SELECT * FROM items")
__all_items__ = []
__generate_list(__all_items__)

__con__.close()


class ItemNotFound(Exception):
    """Exception raised when requested item is not found"""

    def __str__(self) -> str:
        return "Requested item not found"
