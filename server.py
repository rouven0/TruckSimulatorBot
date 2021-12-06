from flask import Flask

app = Flask(__name__)

import asyncio
import api.database as database
import api.players


@app.route("/")
async def hello():
    return vars(await api.players.get(692796548282712074))


if __name__ == "__main__":
    asyncio.run(database.init())
    app.run(port=3000)
    asyncio.run(database.close())
