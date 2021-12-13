"""
This module contains the company class
"""

import logging
from typing import Union
import ressources.database as database
from ressources.players import Player


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

    def __init__(self, name: str, logo: str, hq_position: Union[str, list], founder: int, net_worth: int) -> None:
        self.name = name
        self.logo = logo
        if isinstance(hq_position, str):
            self.hq_position = _get_position(hq_position)
        else:
            self.hq_position = hq_position
        self.founder = founder
        self.net_worth = net_worth

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

    async def add_net_worth(self, amount: int):
        await database.con.execute(
            "UPDATE companies SET net_worth=? WHERE name=?", (self.net_worth + amount, self.name)
        )
        self.net_worth += amount

    async def remove_net_worth(self, amount: int):
        await database.con.execute(
            "UPDATE companies SET net_worth=? WHERE name=?", (self.net_worth - amount, self.name)
        )
        self.net_worth -= amount

    async def get_members(self) -> list[Player]:
        members = []
        cur = await database.con.execute("SELECT * FROM players WHERE company=:name", {"name": self.name})
        member_tuple = await cur.fetchall()
        await cur.close()
        for member in member_tuple:
            members.append(Player(*member))
        return members


async def get(name: str) -> Company:
    cur = await database.con.execute("SELECT * FROM companies WHERE name=:name", {"name": name})
    company_tuple: tuple = await cur.fetchone()
    await cur.close()
    try:
        company = Company(*company_tuple)
        return company
    except TypeError:
        raise CompanyNotFound()


async def get_all() -> list[Company]:
    cur = await database.con.execute("SELECT * from companies")
    companies = []
    for data_tuple in await cur.fetchall():
        companies.append(Company(*data_tuple))
    await cur.close()
    return companies


async def insert(company: Company) -> None:
    await database.con.execute("INSERT INTO companies VALUES (?,?,?,?,?)", tuple(company))
    await database.con.commit()
    logging.info("%s created the company %s", company.founder, company.name)


async def remove(company: Company) -> None:
    await database.con.execute("DELETE FROM companies WHERE name=:name", {"name": company.name})
    await database.con.commit()
    logging.info("Company %s got deleted", company.name)


async def update(
    company: Company, logo: str = None, hq_position: list = None, founder: int = None, net_worth: int = None
) -> None:
    """
    Updates a company in the database
    """
    if logo is not None:
        await database.con.execute("UPDATE companies SET logo=? WHERE name=?", (logo, company.name))
        company.logo = logo
    if hq_position is not None:
        await database.con.execute(
            "UPDATE companies SET hq_position=? WHERE name=?", (_format_pos_to_db(hq_position), company.name)
        )
        company.hq_position = hq_position
    if founder is not None:
        await database.con.execute("UPDATE companies SET founder=? WHERE name=?", (founder, company.name))
        company.founder = founder
    if net_worth is not None:
        await database.con.execute("UPDATE companies SET net_worth=? WHERE name=?", (net_worth, company.name))
        company.net_worth = net_worth
    await database.con.commit()
    logging.debug("Updated company %s to %s", company.name, tuple(company))


class CompanyNotFound(Exception):
    """
    Exception raised when a company isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested company was not found"
