"""
This module contains some functions used to calculate xp, levels and money stuff. Basically just a lot of math.
"""
import math
from random import randint


def coincap(level: int) -> int:
    """
    :param int level: The player's level
    :return: The max amount of coins a player can receive
    """
    return int(1040000 / (1 + math.exp((-level / 20) + 3)) - 40000)


def get_next_xp(level: int) -> int:
    """
    :param int level: The player's level
    :return: The xp need to level up
    """
    return (level + 1) ** 3


def get_job_reward_xp(level: int) -> int:
    """
    :param int level: The player's level
    :return: The xp to give when a job is finished
    """
    return randint(round((level**3) / 20), round((get_next_xp(level) / 6) + 7))
