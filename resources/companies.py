# pylint: disable=attribute-defined-outside-init
"""
Companies are a group of players that collect money together. Every company's logo will appear on the map as emoji.
Every time a player completes a job. The companies net worth is increased.
"""

from dataclasses import dataclass
import logging
from typing import Optional, Union
from resources import database
from resources import position as pos
from resources.players import Player


@dataclass
class Company:
    """
    :ivar int id: Internal company id
    :ivar str name: Name of the company
    :ivar str logo: Emoji displayed as logo on the map
    :ivar str description: A description for that company
    :ivar list hq_position: Position of the company's headquarters
    :ivar str founder: Id of the founder of the company, who has control over it
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

    def __str__(self) -> str:
        return self.name

    def add_net_worth(self, amount: int) -> None:
        """
        Increases a company's net worth

        :param int amount: Amount to be added
        """
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE id=%s", (self.net_worth + amount, self.id))
        self.net_worth += amount

    def remove_net_worth(self, amount: int) -> None:
        """
        Decreases a company's net worth

        :param int amount: Amount to be removed
        """
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE id=%s", (self.net_worth - amount, self.id))
        self.net_worth -= amount

    def get_members(self) -> list[Player]:
        """
        :return: A list of all players that belong to the company
        """
        # Maybe make this a property at some point
        members = []
        database.cur.execute("SELECT * FROM players WHERE company=%s", (self.id,))
        record = database.cur.fetchall()
        for member in record:
            members.append(Player(**member))
        return members


def exists(name: str) -> bool:
    """
    Checks if a company is found in the database

    :param str name: A name to check
    :return: A bool defining whether that company exists
    """
    database.cur.execute("SELECT * FROM companies WHERE name=%s", (name,))
    if len(database.cur.fetchall()) == 1:
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
    database.cur.execute("SELECT * FROM companies WHERE id=%s", (id,))
    record = database.cur.fetchone()
    company = Company(**record)
    return company


def get_all() -> list[Company]:
    """
    :return: A list of all registered companies
    """
    database.cur.execute("SELECT * from companies")
    companies = []
    for record in database.cur.fetchall():
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
    print(sql)
    print(tuple(company))
    database.cur.execute(sql, tuple(company))
    database.con.commit()
    logging.info("%s created the company %s", company.founder, company.name)
    database.cur.execute("Select id from companies where name=%s", (company.name,))
    return database.cur.fetchone()["id"]


def remove(company: Company) -> None:
    """
    Delete a company

    :param Company company: The company to remove
    """
    database.cur.execute("DELETE FROM companies WHERE id=%s", (company.id,))
    database.con.commit()
    logging.info("Company %s got deleted", company.name)


def update(
    company: Company,
    name: str = None,
    logo: str = None,
    description: str = None,
    hq_position: Union[pos.Position, int] = None,
    founder: str = None,
    net_worth: int = None,
) -> None:
    """
    Updates a company in the database

    Same as in players, not documented until fixed
    """
    if name is not None:
        database.cur.execute("UPDATE companies SET name=%s WHERE id=%s", (name, company.id))
        company.name = name
    if logo is not None:
        database.cur.execute("UPDATE companies SET logo=%s WHERE id=%s", (logo, company.id))
        company.logo = logo
    if description is not None:
        database.cur.execute("UPDATE companies SET description=%s WHERE id=%s", (description, company.id))
        company.description = description
    if hq_position is not None:
        if isinstance(hq_position, int):
            hq_position = pos.Position.from_int(hq_position)
        database.cur.execute("UPDATE companies SET hq_position=%s WHERE id=%s", (int(hq_position), company.id))
        company.hq_position = hq_position
    if founder is not None:
        database.cur.execute("UPDATE companies SET founder=%s WHERE id=%s", (founder, company.id))
        company.founder = founder
    if net_worth is not None:
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE id=%s", (net_worth, company.id))
        company.net_worth = net_worth
    database.con.commit()
    logging.debug("Updated company %s to %s", company.name, tuple(company))


class CompanyNotFound(Exception):
    """
    Exception raised when a company isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested company was not found"
