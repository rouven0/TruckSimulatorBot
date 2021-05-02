import config

LEFT="⬅️"
DOWN="⬇️"
UP="⬆️"
RIGHT="➡️"
STOP="\N{OCTAGONAL SIGN}"
LIST_ITEM=":small_orange_diamond:"

def get_drive_position_symbols(position):
    x = position[0]
    y = position[1]
    symbols = []
    if x > 0:
        symbols.append(LEFT)
    if y > 0:
        symbols.append(DOWN)
    if y < config.MAP_BORDER:
        symbols.append(UP)
    if x < config.MAP_BORDER:
        symbols.append(RIGHT)

    symbols.append(STOP)
    return symbols
