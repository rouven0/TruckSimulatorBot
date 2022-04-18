"""
This module contains the position class including some methods to convert the position database-ready
Positions can be turned into a 32-bit integer that is stored in the database

Bit structure:
--------------
    - Bits 0-15: X-value of the position
    - Bits 16-31: Y-value of the position
"""


class Position:
    """
    A class representing a player's position

    :ivar int x: x-position on the map
    :ivar int y: y-position on the map
    """

    def __init__(self, x: int, y: int) -> None:
        self.x: int = x
        self.y: int = y

    @classmethod
    def from_int(cls, database_int: int):
        """
        Transfers a database integer into the position object

        :param int database_int: The integer comming from the database
        """
        return cls(database_int & ((1 << 16) - 1), database_int >> 16)

    def __int__(self) -> int:
        """
        :return: The position as a database-ready int
        """
        return (self.y << 16) + self.x

    def __str__(self) -> str:
        return f"<:right:853352377255854090> {self.x} <:up:853353627383889980> {self.y}"
