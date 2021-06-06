"""
This module provides all symbols and emojis the bots operates with
"""
import config

LEFT="⬅️"
DOWN="⬇️"
UP="⬆️"
RIGHT="➡️"
STOP="\N{OCTAGONAL SIGN}"
LIST_ITEM=":small_orange_diamond:"

def get_drive_position_symbols(position):
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

    symbols.append(STOP)
    return symbols
