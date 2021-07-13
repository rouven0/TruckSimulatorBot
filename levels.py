"""
This module contains some functions used to calculate xp and levels
"""
from random import randint


def get_next_xp(level: int) -> int:
    return (level + 1) ** 3


def get_job_reward_xp(level: int) -> int:
    return randint(round((level ** 3)/20), round((get_next_xp(level)/6) + 7))
