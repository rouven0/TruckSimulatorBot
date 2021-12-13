from flask import Flask, json

import asyncio

from werkzeug.exceptions import HTTPException, abort
import resources.database as database
import resources.players as players
import resources.players as players
import resources.companies as companies


app = Flask(__name__)


@app.route("/players/<int:id>")
async def get_player(id):
    try:
        player = await players.get(id)
        player.company = vars(await companies.get(player.company)) if player.company is not None else None
        return vars(player)
    except players.PlayerNotRegistered:
        abort(404)
    except players.PlayerBlacklisted:
        abort(404)


@app.route("/players/<int:id>/job")
async def get_job(id):
    try:
        player = await players.get(id)
        return vars(await player.get_job())
    except players.PlayerNotRegistered:
        abort(404)
    except players.PlayerBlacklisted:
        abort(404)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


if __name__ == "__main__":
    asyncio.run(database.init())
    app.run()
    asyncio.run(database.close())
