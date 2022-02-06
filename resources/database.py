"""
This module contains the database connection
"""
from os import getenv
import mysql.connector

con: mysql.connector.CMySQLConnection = mysql.connector.connect(
    host=getenv("MYSQL_HOST"),
    user=getenv("MYSQL_USER"),
    passwd=getenv("MYSQL_PASSWORD"),
    database=getenv("MYSQL_DATABASE"),
    charset="utf8mb4",
    collation="utf8mb4_unicode_ci",
    use_unicode=True,
)

cur = con.cursor(dictionary=True)
