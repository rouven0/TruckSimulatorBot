"""
This module contains the truck class and some functions to operate with trucks
"""
from dataclasses import dataclass
import sqlite3


def __generate_list(lst) -> None:
    for tup in __cur__.fetchall():
        lst.append(Truck(*tup))


@dataclass
class Truck:
    """
    Attributes
        truck_id: Id of this Truck, in range of 0 ... best Truck
        name: Name of the Truck or the Trucks brand
        description: Description that is shown to the player
        price: Price the player has to pay to use this Truck
        gas_consumptions: Amount of Gas used per mile
        gas_capacity: Amount of gas the player can fill in the Truck
        image_url: Url of an image that is show to the user
    """

    truck_id: int
    name: str
    description: str
    price: int
    gas_consumption: int
    gas_capacity: int
    loading_capacity: int
    image_url: str
    emoji: str

    def __str__(self) -> str:
        return self.emoji + " " + self.name


def get(truck_id: int) -> Truck:
    """
    Get a truck based on its id
    """
    for truck in __all_trucks__:
        if truck.truck_id == truck_id:
            return truck
    raise TruckNotFound


def get_all() -> list[Truck]:
    """
    Return a list with all trucks
    """
    return __all_trucks__


__con__ = sqlite3.connect("./resources/objects.db")
__cur__ = __con__.cursor()

__cur__.execute("SELECT * FROM trucks")
__all_trucks__ = []
__generate_list(__all_trucks__)

__con__.close()


class TruckNotFound(Exception):
    """Exception raised when requested truck is not found"""

    def __str__(self) -> str:
        return "Requested truck not found"
