from dataclasses import dataclass
import sqlite3

def __generate_list(l):
    for i in cur.fetchall():
        name = i[0]
        emoji = i[1] 
        l.append(Item(name, emoji))
    

@dataclass
class Item:
    name: str
    emoji: str

def get(name):
    for item in __all_items:
        if item.name == name:
            return item
    return None

con = sqlite3.connect('objects.db')
cur = con.cursor()

cur.execute('SELECT * FROM items')
__all_items = []
__generate_list(__all_items)
