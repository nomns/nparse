import asyncio
import json
import logging
import websockets

logging.basicConfig()
LOG = logging.getLogger(__name__)

PLAYER_LOCS = {}

USERS = set()


class PlayerLocation(dict):
    def __init__(self, x, y, z, zone, player, timestamp):
        super(PlayerLocation, self).__init__(
            x=x, y=y, z=z, zone=zone, player=player, timestamp=timestamp
        )
        self.x = x
        self.y = y
        self.z = z
        self.zone = zone
        self.player = player
        self.timestamp = timestamp


def state_event():
    return json.dumps({"type": "state", "locations": PLAYER_LOCS})


def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state(websocket):
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        logging.warning("Notifying state: %s" % message)
        await asyncio.wait([user.send(message) for user in USERS])
                            # if user != websocket])


async def notify_users(websocket):
    if USERS and len(USERS) > 1:  # asyncio.wait doesn't accept an empty list
        message = users_event()
        logging.warning("Notifying users: %s" % message)
        await asyncio.wait([user.send(message) for user in USERS
                            if user != websocket])


async def register(websocket):
    USERS.add(websocket)
    logging.warning("Registering websocket: %s" % websocket.remote_address[0])
    await notify_users(websocket)


async def unregister(websocket):
    USERS.remove(websocket)
    logging.warning("Deregistering websocket: %s" % websocket.remote_address[0])
    await notify_users(websocket)


async def update_loc(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == "location":
                data = data['location']
                zone_name = data.pop('zone').lower()
                player_name = data.pop('player').capitalize()
            if zone_name not in PLAYER_LOCS:
                PLAYER_LOCS[zone_name] = {}
            PLAYER_LOCS[zone_name][player_name] = data
            await notify_state(websocket)
    except websockets.exceptions.ConnectionClosedError:
        logging.warning("client disconnected: %s" % websocket.remote_address[0])
    finally:
        await unregister(websocket)


if __name__ == "__main__":
    start_server = websockets.serve(update_loc, "localhost", 6789)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
