"""
This module contains the company class
"""

import logging
from typing import Union
import resources.database as database
from resources.players import Player


# TODO make these funtions global so I don't have to paste them for every class
def _format_pos_to_db(pos: list) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])


def _get_position(db_pos) -> list:
    """
    Formats the position string from the database into a list what we can operate with
    """
    pos_x = db_pos[: db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/") + 1 :]
    return [int(pos_x), int(pos_y)]


class Company:
    """
    Attributes:
        name: Name of the company
        logo: emoji displayed as logo on the map
        hq_position: position of the company's headquarters
        founder: founder of the company, has control over it
        net_worth: money the company holds
    """

    def __init__(self, name: str, hq_position: Union[list, str], founder: int, **kwargs) -> None:
        self.name = name
        self.hq_position = hq_position

        if isinstance(hq_position, str):
            self.hq_position = _get_position(hq_position)
        else:
            self.hq_position = hq_position
        self.founder = founder
        self.logo = kwargs.pop("logo", f":regional_indicator_{str.lower(name[0])}:")
        self.net_worth = kwargs.pop("net_worth", 0)

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr == "hq_position":
                return _format_pos_to_db(self.__getattribute__(attr))
            else:
                return self.__getattribute__(attr)
        else:
            raise StopIteration

    def __str__(self) -> str:
        return f"{self.name} founded by {self.founder}"

    def add_net_worth(self, amount: int):
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE name=%s", (self.net_worth + amount, self.name))
        self.net_worth += amount

    def remove_net_worth(self, amount: int):
        database.cur.execute("UPDATE companies SET net_worth=%s WHERE name=%s", (self.net_worth - amount, self.name))
        self.net_worth -= amount

    def get_members(self) -> list[Player]:
        members = []
        database.cur.execute("SELECT * FROM players WHERE company=%s", (self.name,))
        members = database.cur.fetchall()
        for member in members:
            members.append(Player(**member))
        return members


def get(name: str) -> Company:
    database.cur.execute("SELECT * FROM companies WHERE name=%s", (name,))
    record = database.cur.fetchone()

    try:
        company = Company(**record))
        return company
    except TypeError:
        raise CompanyNotFound()


def get_all() -> list[Company]:
    cur = database.cur.execute("SELECT * from companies")
    companies = []
    for record in cur.fetchall():
        companies.append(Company(**record))
    return companies


def insert(company: Company) -> None:
    placeholders = ", ".join(["%s"] * len(vars(company)))
    columns = ", ".join(vars(company).keys())
    sql = "INSERT INTO companies (%s) VALUES (%s)" % (columns, placeholders)
    database.cur.execute(sql, tuple(company))
    database.con.commit()
    logging.info("%s created the company %s", company.founder, company.name)


def remove(company: Company) -> None:
    database.cur.execute("DELETE FROM companies WHERE name=%s", (company.name,))
    database.con.commit()
    logging.info("Company %s got deleted", company.name)


def update(
    company: Company, logo: str = None, hq_position: list = None, founder: int = None, net_worth: int = None
) -> None:
    """
    Updates a company in the database
    """
    if logo is not None:
        database.cur.execute("UPDATE companies SET logo=%s WHERE name=%s", (logo, company.name))
        company.logo = logo
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
