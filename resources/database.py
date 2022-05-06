"""
This module contains the database connection
"""
import mysql.connector
import config


def execute(query: str, args=None) -> int:
    """
    Executes a query

    :param str query: The query to execute
    :param args: The arguments to pass to the query
    :returns: the number of rows affected
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(query, args)
            con.commit()
            return con.rowcount


def fetchall(query: str, args=None) -> list[dict]:
    """
    Fetches all results from a query

    :param str query: The query to execute
    :param args: The arguments to pass to the query
    :returns: A list of records as dictionaries
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(query, args)
            return cur.fetchall()


def fetchmany(query: str, args=None, size=None) -> list[dict]:
    """
    Fetches a limited number of results from a query

    :param str query: The query to execute
    :param args: The arguments to pass to the query
    :param size: The number of results to fetch
    :returns: A list of records as dictionaries
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True, buffered=True) as cur:
            cur.execute(query, args)
            return cur.fetchmany(size)


def fetchone(query: str, args=None) -> dict:
    """
    Fetches a single result from a query

    :param str query: The query to execute
    :param args: The arguments to pass to the query
    :returns: A single record as a dictionary
    """
    with mysql.connector.connect(**config.DATABASE_ARGS) as con:
        with con.cursor(dictionary=True, buffered=True) as cur:
            cur.execute(query, args)
            return cur.fetchone()
