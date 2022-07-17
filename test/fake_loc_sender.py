import json
import asyncio
import websockets


HOST = 'ws://localhost:8424'


async def hello():
    async with websockets.connect(HOST) as websocket:
        x = 0
        y = 0
        while True:
            message = {'type': "location",
                       'group_key': 'hi',
                       'location': {
                           'zone': 'west freeport',
                           'player': 'tester2',
                           "x": -101.72 + x,
                           "y": -30.79 + y,
                           "z": -24.25,
                           "timestamp": "2020-08-16T01:44:00.654871"
                       }}
            await websocket.send(json.dumps(message))
            x = (x + 3) % 50
            y = (y + 3) % 50
            await asyncio.sleep(0.5)

asyncio.get_event_loop().run_until_complete(hello())
