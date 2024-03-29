# pylint: disable=attribute-defined-outside-init
"""
Companies are a group of players that collect money together. Every company's logo will appear on the map as emoji.
Every time a player completes a job. The companies net worth is increased.
"""

import inspect
import logging
from dataclasses import dataclass
from typing import Any, Optional

from trucksimulator.resources import database
from trucksimulator.resources import position as pos
from trucksimulator.resources.players import Player


@dataclass
class Company:
    """
    :ivar int id: Internal company id
    :ivar str name: Name of the company
    :ivar str logo: Emoji displayed as logo on the map
    :ivar str description: A description for that company
    :ivar list hq_position: Position of the company's headquarters
    :ivar str founder: ID of the founder of the company
    :ivar int net_worth: Money the company holds
    """

    id: int
    name: str
    hq_position: pos.Position
    founder: str
    description: str = ""
    logo: str = "🏛️"
    net_worth: int = 3000

    def __post_init__(self) -> None:
        if isinstance(self.hq_position, int):
            self.hq_position = pos.Position.from_int(self.hq_position)

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr == "hq_position":
                return int(self.__getattribute__(attr))
            return self.__getattribute__(attr)
        raise StopIteration

    def __setattr__(self, __name: str, __value: Any) -> None:
        """
        Overrides the setattr method to update the database when a value is changed

        :param str __name: Name of the attribute
        :param Any __value: Value of the attribute
        """
        context = inspect.getouterframes(inspect.currentframe())[1][3]
        if context not in ["__init__", "__post_init__", "__next__", "__iter__"]:
            if __name == "hq_position":
                __value_db = int(__value)
            else:
                __value_db = __value
            sql_base = f"UPDATE companies SET {__name}=%s WHERE id=%s"
            database.execute(sql_base, (__value_db, self.id))
        super().__setattr__(__name, __value)

    def __str__(self) -> str:
        return self.name

    def add_net_worth(self, amount: int) -> None:
        """
        Increases a company's net worth

        :param int amount: Amount to be added
        """
        self.net_worth += amount

    def remove_net_worth(self, amount: int) -> None:
        """
        Decreases a company's net worth

        :param int amount: Amount to be removed
        """
        self.net_worth -= amount

    def get_members(self) -> list[Player]:
        """
        :return: A list of all players that belong to the company
        """
        # Maybe make this a property at some point
        members = []
        records = database.fetchall("SELECT * FROM players WHERE company=%s", (self.id,))
        for member in records:
            members.append(Player(**member))
        return members


def exists(name: str) -> bool:
    """
    Checks if a company is found in the database

    :param str name: A name to check
    :return: A bool defining whether that company exists
    """
    records = database.fetchall("SELECT * FROM companies WHERE name=%s", (name,))
    if len(records) == 1:
        return True
    return False


def get(id: Optional[int]) -> Company:
    """
    Gets a company from the database

    :param int id: The desired company's id, can be None
    :raises CompanyNotFound: In case a company with this name doesn't exist
    :return: The desired company
    """
    if not id:
        raise CompanyNotFound()
    record = database.fetchone("SELECT * FROM companies WHERE id=%s", (id,))
    company = Company(**record)
    return company


def get_all() -> list[Company]:
    """
    :return: A list of all registered companies
    """
    records = database.fetchall("SELECT * from companies")
    companies = []
    for record in records:
        companies.append(Company(**record))
    return companies


def insert(company: Company) -> int:
    """
    Add a new company

    :param Company company: The company to insert
    :return: The company's id
    """
    attrs = vars(company)
    attrs.pop("id")
    placeholders = ", ".join(["%s"] * len(attrs))
    columns = ", ".join(attrs.keys())
    sql = f"INSERT INTO companies ({columns}) VALUES ({placeholders})"
    database.execute(sql, tuple(company))
    logging.info("%s created the company %s", company.founder, company.name)
    return database.fetchone("Select id from companies where name=%s", (company.name,))["id"]


def remove(company: Company) -> None:
    """
    Delete a company

    :param Company company: The company to remove
    """
    database.execute("DELETE FROM companies WHERE id=%s", (company.id,))
    logging.info("Company %s got deleted", company.name)


class CompanyNotFound(Exception):
    """
    Exception raised when a company isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested company was not found"
