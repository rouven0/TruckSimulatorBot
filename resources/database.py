"""
This module contains the database connection
"""
import mysql.connector
import config


def execute(query: str, args=None) -> None:
    """
    Executes a query
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(query, args)
            con.commit()


def fetchall(query: str, args=None) -> list:
    """
    Fetches all results from a query
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(query, args)
            return cur.fetchall()


def fetchmany(query: str, args=None, size=None) -> list:
    """
    Fetches a limited number of results from a query
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(query, args)
            return cur.fetchmany(size)


def fetchone(query: str, args=None) -> dict:
    """
    Fetches a single result from a query
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(query, args)
            return cur.fetchone()
