"""
This module provides the Job class and all the methods to operate with jobs in the database
"""
from dataclasses import dataclass
import sqlite3
from random import randint
from math import sqrt
from players import Player
import places
import items

__con__ = sqlite3.connect('players.db')
__cur__ = __con__.cursor()

STATE_CLAIMED = 0
STATE_LOADED = 1
STATE_DONE = 2


@dataclass
class Job:
    """
    Attributes:
        player_id: Player id that this jobs belongs to
                   Used as primary key in the database
        place_from: Place from which the player has to take the items
        place_to: Place the player has to drive to when the truck is loaded
        state: current state, see get_state() for more information about the states
        reward: Amount of money the player gets for this job

    """
    player_id: int
    place_from: places.Place
    place_to: places.Place
    state: int
    reward: int


def __from_tuple(tup) -> Job:
    """
    Returns a Job object from a received database tuple
    """
    return Job(tup[0], places.get(tup[1]), places.get(tup[2]), tup[3], tup[4])


def __to_tuple(job) -> tuple:
    """
    Transforms the job object into a tuple that can be inserted in the db
    """
    return (job.player_id, __format_pos_to_db(job.place_from.position),
            __format_pos_to_db(job.place_to.position), job.state, job.reward)


def __format_pos_to_db(pos) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])


def insert(job: Job) -> None:
    """
    Inserts a Job object into the players database
    """
    __cur__.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', __to_tuple(job))
    __con__.commit()


def remove(job: Job) -> None:
    """
    Removes a job from the player database
    """
    __cur__.execute('DELETE FROM jobs WHERE player_id=:id', {"id": job.player_id})
    __con__.commit()


def update(job: Job, state=None) -> None:
    """
    Updates a job's state
    """
    if state is not None:
        __cur__.execute('UPDATE jobs SET state=? WHERE player_id=?', (state, job.player_id))
    __con__.commit()


def get(user_id) -> Job:
    # TODO better up job getting using exceptions and has_job(): -> boolean
    """
    Get the Players current job as Job object
    """
    __cur__.execute("SELECT * FROM jobs WHERE player_id=:id", {"id": user_id})
    try:
        return __from_tuple(__cur__.fetchone())
    except TypeError:
        return None


def generate(player: Player) -> tuple:
    """
    This takes two random places from the list, calculates its reward based on the miles the player
    has to drive and returns the Job object and the job as a string in human readable format.
    """
    available_places = places.get_quest_active().copy()
    place_from = available_places[randint(0, len(available_places) - 1)]
    item = items.get(place_from.produced_item)
    available_places.remove(place_from)
    place_to = available_places[randint(0, len(available_places) - 1)]
    arrival_miles_x = abs(player.position[0] - place_from.position[0])
    arrival_miles_y = abs(player.position[1] - place_from.position[1])
    arrival_reward = round(sqrt(arrival_miles_x ** 2 + arrival_miles_y ** 2) * 14)
    job_miles_x = abs(place_from.position[0] - place_to.position[0])
    job_miles_y = abs(place_from.position[1] - place_to.position[1])
    job_reward = round(sqrt(job_miles_x ** 2 + job_miles_y ** 2) * 79)
    reward = round((job_reward + arrival_reward) * sqrt(player.level+1))
    if reward > 4329*(player.level+1):
        reward = 4329*(player.level+1)
    new_job = Job(player.user_id, place_from, place_to, 0, reward)
    insert(new_job)
    return (new_job,
            "{} needs {} {} from {}. You get ${} for this transport".format(place_to.name, item.emoji, item.name, place_from.name, reward))


def show(job: Job) -> str:
    """
    Prints out the current job in a human readable format
    """
    place_from = job.place_from
    place_to = job.place_to
    item = items.get(place_from.produced_item)
    return "Bring {} {} from {} to {}.".format(item.emoji, item.name, place_from.name, place_to.name)


def get_state(job: Job) -> str:
    """
    Returns the next instructions based on the current jobs state
    """
    if job.state == 0:
        return "You claimed this job. Drive to {} and load your truck with `t.load`".format(job.place_from.name)
    if job.state == 1:
        return "You loaded your truck with the needed items. Now drive to {} and unload them with `t.unload`".format(
            job.place_to.name)
    if job.state == 2:
        return "Your job is done and you got ${}.".format(job.reward)
    return "Something went wrong"
