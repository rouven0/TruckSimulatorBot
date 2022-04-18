# pylint: disable=attribute-defined-outside-init
"""
Jobs are the main way to get money. For every job, the player has to bring items from one place to another.
After the job is done, the reward is payed out.
"""
from dataclasses import dataclass
from random import randint
from math import sqrt
from time import time
from resources import database
from resources import places

STATE_CLAIMED = 0
STATE_LOADED = 1
STATE_DONE = 2


@dataclass
class Job:
    """
    :ivar str player_id: Player id that this jobs belongs to used as primary key in the database
    :ivar places.Place place_from: Place from which the player has to take the items
    :ivar places.Place place_to: Place the player has to drive to when the truck is loaded
    :ivar int state: current state, see get_state() for more information about the states
    :ivar int reward: Amount of money the player gets for this job
    :ivar int create_time: timestamp this job was created
    """

    player_id: str
    place_from: places.Place
    place_to: places.Place
    state: int
    reward: int
    create_time: int

    def __post_init__(self) -> None:
        if isinstance(self.place_from, int):
            self.place_from = places.get(self.place_from)
        if isinstance(self.place_to, int):
            self.place_to = places.get(self.place_to)

    def __iter__(self):
        self._n = 0
        return self

    @property
    def target_place(self) -> places.Place:
        """
        :return: The next place the player has to drive to
        """
        return self.place_from if self.state == 0 else self.place_to

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            if attr in ["place_from", "place_to"]:
                return int(self.__getattribute__(attr).position)
            return self.__getattribute__(attr)
        raise StopIteration


def generate(player) -> Job:
    """
    This takes two random places from the list, calculates its reward based on the miles the player
    has to drive and returns the Job object and the job as a string in human readable format.

    :param players.Player player: Player that this job belongs to
    :return: The full job
    """
    available_places = places.get_all().copy()
    place_from = available_places[randint(0, len(available_places) - 1)]
    available_places.remove(place_from)
    place_to = available_places[randint(0, len(available_places) - 1)]
    arrival_miles_x = abs(player.position.x - place_from.position.x)
    arrival_miles_y = abs(player.position.y - place_from.position.y)
    arrival_reward = round(sqrt(arrival_miles_x ** 2 + arrival_miles_y ** 2) * 14)
    job_miles_x = abs(place_from.position.x - place_to.position.x)
    job_miles_y = abs(place_from.position.y - place_to.position.y)
    job_reward = round(sqrt(job_miles_x ** 2 + job_miles_y ** 2) * 79)
    reward = round((job_reward + arrival_reward) * (player.level + 1))
    new_job = Job(player.id, place_from, place_to, 0, reward, int(time()))
    return new_job


def get_state(job: Job) -> str:
    """
    Returns the next instructions based on the current jobs state

    :param Job job: The job to be looked ot
    :return: The message containing the instructions
    """
    if job.state == 0:
        return f"You claimed this job. Drive to {job.place_from} and load your truck"
    if job.state == 1:
        return f"You loaded your truck with the needed items. Now drive to {job.place_to} and unload them"
    if job.state == 2:
        return f"Your job is done and you got ${job.reward:,}."
    return "Something went wrong"


def get_all() -> list[Job]:
    """
    :return: A list of all running jobs
    """
    # update the connection in case of the timeout-thread doing something
    database.con.commit()
    database.cur.execute("SELECT * FROM jobs")
    all_jobs = []
    record = database.cur.fetchall()
    for job in record:
        all_jobs.append(Job(**job))
    return all_jobs
