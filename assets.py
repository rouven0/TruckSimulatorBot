"""
This file conatins some of the image urls that the bot uses
The images are hosted on a discord server
"""
from random import randint

__DEFAULT_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/837784531267223552/837785502127489064/default.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458133378105404/default_2.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458157608730654/default_3.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458177586593852/default_4.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458205679779901/default_5.png"
]

def get_default():
    """
    Returns a randomly chosen image from the list
    """
    return __DEFAULT_DRIVE_IMAGE_LIST[randint(0, len(__DEFAULT_DRIVE_IMAGE_LIST)-1)]
