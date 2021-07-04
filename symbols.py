"""
This module provides all symbols and emojis the bots operates with
"""
import config

LEFT = 853353650491752459
DOWN = 853353650905677884
UP = 853353627383889980
RIGHT = 853352377255854090
STOP = 853362422298968104
LOAD = 861353140476706877
UNLOAD = 861353156902256680
LIST_ITEM = ":small_orange_diamond:"


def get_drive_position_symbols(position) -> list:
    """
    Returns a list of emojis that the bot will react with to the drive message
    Corresponding arrow symbols will be removed when the map border is reached
    """
    pos_x = position[0]
    pos_y = position[1]
    symbols = []
    if pos_x > 0:
        symbols.append(LEFT)
    if pos_y > 0:
        symbols.append(DOWN)
    if pos_y < config.MAP_BORDER:
        symbols.append(UP)
    if pos_x < config.MAP_BORDER:
        symbols.append(RIGHT)
    return symbols
