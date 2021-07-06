"""
This module contains some functions used to calculate xp and levels
"""


def get_next_xp(level: int) -> int:
    return (level + 1) ** 3
