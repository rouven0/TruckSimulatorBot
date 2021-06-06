from dataclasses import dataclass
import sqlite3
from random import randint
from math import sqrt
from players import Player
import places
import items

__con__ = sqlite3.connect('players.db')
__cur__ = __con__.cursor()

def __from_tuple(tup):
    """
    Returns a Job object from a received database tuple
    """
    return Job(tup[0], places.get(tup[1]), places.get(tup[2]), tup[3], tup[4])

def __to_tuple(job):
    """
    Transforms the job object into a tuple that can be inserted in the db
    """
    return (job.player_id, __format_pos_to_db(job.place_from.position),
            __format_pos_to_db(job.place_to.position), job.state, job.reward)

def __get_position(db_pos):
    """
    Parses the position from the database as list [x][y]
    """
    pos_x = db_pos[:db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/")+1:]
    return [int(pos_x), int(pos_y)]

def __format_pos_to_db(pos):
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])


@dataclass
class Job():
    player_id: int
    place_from: places.Place
    place_to: places.Place
    state: int
    reward: int

def insert(job: Job):
    __cur__.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', __to_tuple(job))
    __con__.commit()

def remove(job :Job):
    __cur__.execute('DELETE FROM jobs WHERE player_id=:id', {"id": job.player_id})
    __con__.commit()

def update(job: Job, state=None):
    if state is not None:
        __cur__.execute('UPDATE jobs SET state=? WHERE player_id=?', (state, job.player_id))
    __con__.commit()

def get(user_id):
    __cur__.execute("SELECT * FROM jobs WHERE player_id=:id", {"id": user_id})
    try:
        return __from_tuple(__cur__.fetchone())
    except TypeError:
        return None

def generate(player: Player):
    available_places = places.get_quest_active().copy()
    place_from = available_places[randint(0, len(available_places) - 1)]
    item = items.get(place_from.produced_item)
    available_places.remove(place_from)
    place_to = available_places[randint(0, len(available_places) - 1)]
    arrival_miles_x = abs(player.position[0] - place_from.position[0])
    arrival_miles_y = abs(player.position[1] - place_from.position[1])
    arrival_reward = round(sqrt(arrival_miles_x**2 + arrival_miles_y**2)*14)
    job_miles_x = abs(place_from.position[0] - place_to.position[0])
    job_miles_y = abs(place_from.position[1] - place_to.position[1])
    job_reward = round(sqrt(job_miles_x**2 + job_miles_y**2)*37)
    reward = job_reward + arrival_reward
    if reward > 4329:
        reward = 4329
    new_job = Job(player.user_id, place_from, place_to, 0, reward)
    insert(new_job)
    return (new_job , "{} needs {} {} from {}. You get ${} for this transport".format(place_to.name,
        item.emoji, item.name, place_from.name, reward))

def show(job: Job):
    place_from = job.place_from
    place_to = job.place_to
    item = items.get(place_from.produced_item)
    return "Bring {} {} from {} to {}.".format(item.emoji, item.name, place_from.name, place_to.name)

def get_state(job: Job):
    if job.state == 0:
        return "You claimed this job. Drive to {} and load your truck with `t.load`".format(job.place_from.name)
    if job.state == 1:
        return "You loaded your truck with the needed items. Now drive to {} and unload them with `t.unload`".format(job.place_to.name)
    if job.state == 2:
        return "Your job is done and you got ${}.".format(job.reward)
    return "Something went wrong"
