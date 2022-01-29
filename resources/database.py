"""
This module contains the database connection
"""
from os import getenv
import mysql.connector

con = mysql.connector.connect(
    host=getenv("MYSQL_HOST"),
    user=getenv("MYSQL_USER"),
    passwd=getenv("MYSQL_PASSWORD"),
    database=getenv("MYSQL_DATABASE"),
)
cur = con.cursor(dictionary=True)
