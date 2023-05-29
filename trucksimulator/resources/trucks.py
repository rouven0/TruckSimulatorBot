"""
Every player has a truck. For now these trucks are static.
"""
import sqlite3
from dataclasses import dataclass
from trucksimulator import config


def __generate_list(lst) -> None:
    for tup in __cur__.fetchall():
        lst.append(Truck(*tup))


@dataclass
class Truck:
    """
    :ivar int truck_id: Id of this Truck, in range of 0 ... best Truck
    :ivar str name: Name of the Truck or the Trucks brand
    :ivar str description: Description that is shown to the player
    :ivar int price: Price the player has to pay to use this Truck
    :ivar int gas_consumptions: Amount of Gas used per mile
    :ivar int gas_capacity: Amount of gas the player can fill in the Truck
    """

    truck_id: int
    name: str
    description: str
    price: int
    gas_consumption: int
    gas_capacity: int
    loading_capacity: int
    emoji: str

    def __str__(self) -> str:
        return self.emoji + " " + self.name


def get(truck_id: int) -> Truck:
    """
    Get a truck based on its id

    :param int truck_id: Id to look for
    :raises TruckNotFound: In case a truck with the requested id doesn't exist
    :return: The corresponding truck
    """
    for truck in __all_trucks__:
        if truck.truck_id == truck_id:
            return truck
    raise TruckNotFound()


def get_all() -> list[Truck]:
    """
    :return: A list containing all trucks
    """
    return __all_trucks__


__con__ = sqlite3.connect(config.BASE_PATH + "/resources/objects.db")
__cur__ = __con__.cursor()

__cur__.execute("SELECT * FROM trucks")
__all_trucks__ = []
__generate_list(__all_trucks__)

__con__.close()


class TruckNotFound(Exception):
    """Exception raised when requested truck is not found"""

    def __str__(self) -> str:
        return "Requested truck not found"
