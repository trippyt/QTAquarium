from quart import Quart, request, websocket
from quart.json import jsonify
import asyncio
import utils
from time import sleep
app = Quart(__name__)


@app.websocket('/temp')
async def temp():
    while True:
        temp = await utils.tank_temperature(temp_c)
        print(temp)
        await asyncio.sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
