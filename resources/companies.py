# pylint: disable=attribute-defined-outside-init
"""
Companies are a group of players that collect money together. Every company's logo will appear on the map as emoji.
Every time a player completes a job. The companies net worth is increased.
"""

import logging
from typing import Optional, Union
from resources import database
from resources.players import Player


def _format_pos_to_db(pos: list) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return f"{pos[0]}/{pos[1]}"


def _get_position(db_pos) -> list:
    """
    Formats the position string from the database into a list what we can operate with
    """
    pos_x = db_pos[: db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/") + 1 :]
    return [int(pos_x), int(pos_y)]


class Company:
    """
    :ivar str name: Name of the company
    :ivar str logo: Emoji displayed as logo on the map
    :ivar str description: A description for that company
    :ivar list hq_position: Position of the company's headquarters
    :ivar str founder: Id of the founder of the company, who has control over it
    :ivar int net_worth: Money the company holds
    """

    def __init__(self, name: str, hq_position: Union[list, str], founder: str, **kwargs) -> None:
        self.name = name
        self.hq_position = hq_position

        if isinstance(hq_position, str):
            self.hq_position = _get_position(hq_position)
        else:
            self.hq_position = hq_position
        self.founder = founder
        self.logo = kwargs.pop("logo", "🏛️")
        self.description = kwargs.pop("description", "")
        self.net_worth = kwargs.pop("net_worth", 3000)

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr == "hq_position":
                return _format_pos_to_db(self.__getattribute__(attr))
            return self.__getattribute__(attr)
        raise StopIteration

    def __str__(self) -> str:
        return self.name

    def add_net_worth(self, amount: int) -> None:
        """
        Increases a company's net worth

        :param int amount: Amount to be added
        """
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE name=%s", (self.net_worth + amount, self.name))
        self.net_worth += amount

    def remove_net_worth(self, amount: int) -> None:
        """
        Decreases a company's net worth

        :param int amount: Amount to be removed
        """
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE name=%s", (self.net_worth - amount, self.name))
        self.net_worth -= amount

    def get_members(self) -> list[Player]:
        """
        :return: A list of all players that belong to the company
        """
        # Maybe make this a property at some point
        members = []
        database.cur.execute("SELECT * FROM players WHERE company=%s", (self.name,))
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


def get(name: Optional[str]) -> Company:
    """
    Gets a company from the database

    :param str name: The desired company's name, can be None
    :raises CompanyNotFound: In case a company with this name doesn't exist
    :return: The desired company
    """
    if name is None or not exists(name):
        raise CompanyNotFound()
    database.cur.execute("SELECT * FROM companies WHERE name=%s", (name,))
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


def insert(company: Company) -> None:
    """
    Add a new company

    :param Company company: The company to insert
    """
    placeholders = ", ".join(["%s"] * len(vars(company)))
    columns = ", ".join(vars(company).keys())
    sql = f"INSERT INTO companies ({columns}) VALUES ({placeholders})"
    database.cur.execute(sql, tuple(company))
    database.con.commit()
    logging.info("%s created the company %s", company.founder, company.name)


def remove(company: Company) -> None:
    """
    Delete a company

    :param Company company: The company to remove
    """
    database.cur.execute("DELETE FROM companies WHERE name=%s", (company.name,))
    database.con.commit()
    logging.info("Company %s got deleted", company.name)


def update(
    company: Company,
    name: str = None,
    logo: str = None,
    description: str = None,
    hq_position: list = None,
    founder: str = None,
    net_worth: int = None,
) -> None:
    """
    Updates a company in the database

    Same as in players, not documented until fixed
    """
    if name is not None:
        database.cur.execute("UPDATE companies SET name=%s WHERE name=%s", (name, company.name))
        database.cur.execute("UPDATE players SET company=%s WHERE company=%s", (name, company.name))
        company.name = name
    if logo is not None:
        database.cur.execute("UPDATE companies SET logo=%s WHERE name=%s", (logo, company.name))
        company.logo = logo
    if description is not None:
        database.cur.execute("UPDATE companies SET description=%s WHERE name=%s", (description, company.name))
        company.description = description
    if hq_position is not None:
        database.cur.execute(
            "UPDATE companies SET hq_position=%s WHERE name=%s", (_format_pos_to_db(hq_position), company.name)
        )
        company.hq_position = hq_position
    if founder is not None:
        database.cur.execute("UPDATE companies SET founder=%s WHERE name=%s", (founder, company.name))
        company.founder = founder
    if net_worth is not None:
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE name=%s", (net_worth, company.name))
        company.net_worth = net_worth
    database.con.commit()
    logging.debug("Updated company %s to %s", company.name, tuple(company))


class CompanyNotFound(Exception):
    """
    Exception raised when a company isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested company was not found"
