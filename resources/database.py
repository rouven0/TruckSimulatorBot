"""
This module contains the database connection
"""
import aiosqlite
import logging


async def init():
    global con
    con = await aiosqlite.connect("./resources/players.db")
    logging.info("Initialized player database")


async def close():
    await con.close()
    logging.info("Closed player database connection")
