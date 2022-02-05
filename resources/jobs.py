"""
This module provides the Job class and all the methods to operate with jobs in the database
"""
from random import randint
from math import sqrt
from time import time
import resources.places as places

STATE_CLAIMED = 0
STATE_LOADED = 1
STATE_DONE = 2


def _format_pos_to_db(pos) -> str:
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])


class Job:
    """
    Attributes:
        player_id: Player id that this jobs belongs to
                   Used as primary key in the database
        place_from: Place from which the player has to take the items
        place_to: Place the player has to drive to when the truck is loaded
        state: current state, see get_state() for more information about the states
        reward: Amount of money the player gets for this job
        create_time: timestamp this job was created
    """

    def __init__(
        self,
        player_id: int,
        place_from: places.Place,
        place_to: places.Place,
        state: int,
        reward: int,
        create_time: int,
    ) -> None:
        self.player_id = player_id
        if isinstance(place_from, str):
            self.place_from = places.get(place_from)
            self.place_to = places.get(place_to)
        else:
            self.place_from = place_from
            self.place_to = place_to
        self.state = state
        self.reward = reward
        self.create_time = create_time

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr in ["place_from", "place_to"]:
                return _format_pos_to_db(self.__getattribute__(attr).position)
            else:
                return self.__getattribute__(attr)
        else:
            raise StopIteration


def generate(player) -> Job:
    """
    This takes two random places from the list, calculates its reward based on the miles the player
    has to drive and returns the Job object and the job as a string in human readable format.
    """
    available_places = places.get_public().copy()
    place_from = available_places[randint(0, len(available_places) - 1)]
    available_places.remove(place_from)
    place_to = available_places[randint(0, len(available_places) - 1)]
    arrival_miles_x = abs(player.position[0] - place_from.position[0])
    arrival_miles_y = abs(player.position[1] - place_from.position[1])
    arrival_reward = round(sqrt(arrival_miles_x ** 2 + arrival_miles_y ** 2) * 14)
    job_miles_x = abs(place_from.position[0] - place_to.position[0])
    job_miles_y = abs(place_from.position[1] - place_to.position[1])
    job_reward = round(sqrt(job_miles_x ** 2 + job_miles_y ** 2) * 79)
    reward = round((job_reward + arrival_reward) * (player.level + 1))
    new_job = Job(player.id, place_from, place_to, 0, reward, int(time()))
    return new_job


def get_state(job: Job) -> str:
    """
    Returns the next instructions based on the current jobs state
    """
    if job.state == 0:
        return "You claimed this job. Drive to {} and load your truck".format(job.place_from.name)
    if job.state == 1:
        return "You loaded your truck with the needed items. Now drive to {} and unload them".format(job.place_to.name)
    if job.state == 2:
        return "Your job is done and you got ${:,}.".format(job.reward)
    return "Something went wrong"
