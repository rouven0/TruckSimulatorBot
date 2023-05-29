"""
This file contains some of the image urls that the bot uses
"""

from trucksimulator import config


def get(route: str) -> str:
    """
    Return an image url based on the image server configured
    """
    return config.IMAGE_HOST + route
