"""
This file contains some of the image urls that the bot uses
The images are hosted on a discord server
"""
from ressources.places import Place
from ressources.players import Player
from random import randint

__DEFAULT_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/868845783225622559/868846294406418432/default_1-default_truck.png",
    "https://cdn.discordapp.com/attachments/868845805606424607/868846408722182205/default_2-default_truck.png",
    "https://cdn.discordapp.com/attachments/868845802141913118/868846461817851964/default_3-default_truck.png",
    "https://cdn.discordapp.com/attachments/868845857028579368/868846576607576114/default_4-default_truck.png",
    "https://cdn.discordapp.com/attachments/868845874015522827/868846632257585172/default_5-default_truck.png",
]

__JUNGLE_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/868845783225622559/868846297837350912/default_1-jungle_truck.png",
    "https://cdn.discordapp.com/attachments/868845805606424607/868846413142962196/default_2-jungle_truck.png",
    "https://cdn.discordapp.com/attachments/868845802141913118/868846466989436928/default_3-jungle_truck.png",
    "https://cdn.discordapp.com/attachments/868845857028579368/868846581363912704/default_4-jungle_truck.png",
    "https://cdn.discordapp.com/attachments/868845874015522827/868846637399805982/default_5-jungle_truck.png",
]

__TROPICAL_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/868845783225622559/868846298558791680/default_1-tropical_breeze_truck.png",
    "https://cdn.discordapp.com/attachments/868845805606424607/868846414636126228/default_2-tropical_breeze_truck.png",
    "https://cdn.discordapp.com/attachments/868845802141913118/868846468683952168/default_3-tropical_breeze_truck.png",
    "https://cdn.discordapp.com/attachments/868845857028579368/868846583603666954/default_4-tropical_breeze_truck.png",
    "https://cdn.discordapp.com/attachments/868845874015522827/868846639203364905/default_5-tropical_breeze_truck.png",
]

__HELL_DRIVE_IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/868845783225622559/868846296541331476/default_1-hell_truck.png",
    "https://cdn.discordapp.com/attachments/868845805606424607/868846411616235520/default_2-hell_truck.png",
    "https://cdn.discordapp.com/attachments/868845802141913118/868846464531570708/default_3-hell_truck.png",
    "https://cdn.discordapp.com/attachments/868845857028579368/868846578943807488/default_4-hell_truck.png",
    "https://cdn.discordapp.com/attachments/868845874015522827/868846634996494346/default_5-hell_truck.png",
]


def get_default(player: Player) -> str:
    """
    Returns a randomly chosen image from the list
    """
    if player.truck_id == 1:
        lst = __JUNGLE_DRIVE_IMAGE_LIST
    elif player.truck_id == 2:
        lst = __TROPICAL_DRIVE_IMAGE_LIST
    elif player.truck_id == 3:
        lst = __HELL_DRIVE_IMAGE_LIST
    else:
        lst = __DEFAULT_DRIVE_IMAGE_LIST

    return lst[randint(0, len(lst) - 1)]


def get_place_image(player: Player, place: Place) -> str:
    """
    Returns the places image url depending on the players truck
    """
    if player.truck_id == 1:
        url = place.image_url_jungle
    elif player.truck_id == 2:
        url = place.image_url_tropical
    elif player.truck_id == 3:
        url = place.image_url_hell
    else:
        url = place.image_url_default
    return url
