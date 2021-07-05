"""
This file contains some of the image urls that the bot uses
The images are hosted on a discord server
"""
from places import Place
from random import randint
from players import Player

__DEFAULT_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/837784531267223552/837785502127489064/default.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458133378105404/default_2.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458157608730654/default_3.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458177586593852/default_4.png",
    "https://cdn.discordapp.com/attachments/837784531267223552/838458205679779901/default_5.png"
]

__BETTER_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/861619885218332713/861634347094638612/default_better.png",
    "https://cdn.discordapp.com/attachments/861619885218332713/861634327904780388/default_2_better.png",
    "https://cdn.discordapp.com/attachments/861619885218332713/861634332959309864/default_3_better.png",
    "https://cdn.discordapp.com/attachments/861619885218332713/861634337484963871/default_4_better.png",
    "https://cdn.discordapp.com/attachments/861619885218332713/861634342199754782/default_5_better.png"
]

__TROPICAL_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/861619927185489931/861634126247624734/default_tropical.png",
    "https://cdn.discordapp.com/attachments/861619927185489931/861634112288063538/default_2_tropical.png",
    "https://cdn.discordapp.com/attachments/861619927185489931/861634115698294794/default_3_tropical.png",
    "https://cdn.discordapp.com/attachments/861619927185489931/861634118928695356/default_4_tropical.png",
    "https://cdn.discordapp.com/attachments/861619927185489931/861634122636460032/default_5_tropical.png"
]

__ULTIMATE_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/861619966137860118/861634997403779092/default_ultimatre.png",
    "https://cdn.discordapp.com/attachments/861619966137860118/861634981683003411/default_2_ultimate.png",
    "https://cdn.discordapp.com/attachments/861619966137860118/861634986011394068/default_3_ultimate.png",
    "https://cdn.discordapp.com/attachments/861619966137860118/861634990025211934/default_4_ultimate.png", 
    "https://cdn.discordapp.com/attachments/861619966137860118/861634993738350612/default_5_ultimate.png"

]


def get_default(player: Player) -> str:
    """
    Returns a randomly chosen image from the list
    """
    if player.truck_id == 1:
        lst = __BETTER_DRIVE_IMAGE_LIST
    elif player.truck_id == 2:
        lst = __TROPICAL_DRIVE_IMAGE_LIST
    elif player.truck_id == 3:
        lst = __ULTIMATE_DRIVE_IMAGE_LIST
    else:
        lst = __DEFAULT_DRIVE_IMAGE_LIST

    return lst[randint(0, len(lst) - 1)]

def get_place_image(player: Player, place: Place) -> str:
    """
    Returns the places image url depending on the players truck
    """
    if player.truck_id == 1:
        url = place.image_url_better
    elif player.truck_id == 2:
        url = place.image_url_tropical
    elif player.truck_id == 3:
        url = place.image_url_ultimate
    else:
        url = place.image_url
    return url
