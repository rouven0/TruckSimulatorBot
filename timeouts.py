from time import time, sleep
import logging
import requests
from dotenv import load_dotenv

import config
from resources import players
from resources import jobs

load_dotenv("./.env")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)

while True:
    for player in players.get_all_driving_players():
        if time() - player.last_action_time > 840:
            logging.info("Driving of %s timed out", player.name)
            requests.patch(url=player.followup_url + "/messages/@original", json={"components": []})
            player.stop_drive()

    for job in jobs.get_all():
        if time() - job.create_time > 604800:
            player = players.get(job.player_id)
            player.remove_job(job)
            logging.info("Deleted a job by player %s", player.name)

    sleep(5)
