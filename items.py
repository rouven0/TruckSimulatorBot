"""
This module provides the item class and a list of items, easy to access with get()
"""
from dataclasses import dataclass
import sqlite3


@dataclass
class Item:
    name: str
    emoji: str


def __generate_list(lst) -> None:
    for i in __cur__.fetchall():
        name = i[0]
        emoji = i[1]
        lst.append(Item(name, emoji))


def get(name) -> Item:
    for item in __all_items__:
        if item.name == name:
            return item
    raise ItemNotFound()

__con__ = sqlite3.connect('objects.db')
__cur__ = __con__.cursor()

__cur__.execute('SELECT * FROM items')
__all_items__ = []
__generate_list(__all_items__)

__con__.close()


class ItemNotFound(Exception):
    "Exception raised when requested item is not found"
    def __str__(self) -> str:
        return "Requested item not found"
