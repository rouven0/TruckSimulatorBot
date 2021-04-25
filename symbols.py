def get_drive_position_symbols(position):
    x = position[0]
    y = position[1]
    max_x = 16
    max_y = 16
    symbols = []
    if x > 0:
        symbols.append("\N{LEFTWARDS BLACK ARROW}")
    if y > 0:
        symbols.append("\N{DOWNWARDS BLACK ARROW}")
    if y < max_y:
        symbols.append("\N{UPWARDS BLACK ARROW}")
    if x < max_x:
        symbols.append("\N{BLACK RIGHTWARDS ARROW}")

    symbols.append("\N{OCTAGONAL SIGN}")
    return symbols
