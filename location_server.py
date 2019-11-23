import asyncio
import json
import logging

import websockets

logging.basicConfig()
LOG = logging.getLogger(__name__)

# Update these variables to change the listening interface/port.
BIND_HOST = "0.0.0.0"
BIND_PORT = 8424

PLAYERS = set()
PLAYER_LOCS = {}


# TODO: Move this to some central location and use it for both server+client.
# Subclassing dict allows this object to seamlessly json-encode.
class PlayerLocation(dict):
    def __init__(self, x, y, z, zone, player, timestamp):
        super(PlayerLocation, self).__init__(
            x=x, y=y, z=z, zone=zone, player=player, timestamp=timestamp)
        self.x = x
        self.y = y
        self.z = z
        self.zone = zone
        self.player = player
        self.timestamp = timestamp


def location_event():
    return json.dumps({"type": "state", "locations": PLAYER_LOCS})


def users_event():
    return json.dumps({"type": "users", "count": len(PLAYERS)})


async def notify_location(websocket):
    # TODO: Enforce a maximum update frequency to avoid spamming with large
    #       numbers of players connected and sending updates.
    if PLAYERS and len(PLAYERS) > 1:
        message = location_event()
        logging.warning("Notifying locations: %s" % message)
        await asyncio.wait([user.send(message) for user in PLAYERS
                            if user != websocket])


async def notify_users(websocket):
    if PLAYERS and len(PLAYERS) > 1:
        message = users_event()
        logging.warning("Notifying players: %s" % message)
        await asyncio.wait([user.send(message) for user in PLAYERS
                            if user != websocket])


async def register(websocket):
    PLAYERS.add(websocket)
    logging.warning("Registering player: %s" % websocket.remote_address[0])
    await notify_users(websocket)


async def unregister(websocket):
    PLAYERS.remove(websocket)
    logging.warning("Deregistering player: %s" % websocket.remote_address[0])
    await notify_users(websocket)


async def update_loc(websocket, path):
    await register(websocket)
    try:
        await notify_location(websocket)
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == "location":
                data = data['location']
                zone_name = data.pop('zone').lower()
                player_name = data.pop('player').capitalize()
            if zone_name not in PLAYER_LOCS:
                PLAYER_LOCS[zone_name] = {}
            remove_player_from_zones(player_name, except_zone=zone_name)
            PLAYER_LOCS[zone_name][player_name] = data
            await notify_location(websocket)
    except websockets.exceptions.ConnectionClosedError:
        logging.warning(
            "Player disconnected: %s" % websocket.remote_address[0])
    finally:
        await unregister(websocket)


def remove_player_from_zones(name, except_zone=None):
    for zone in PLAYER_LOCS:
        if zone == except_zone:
            continue
        if name in PLAYER_LOCS[zone]:
            PLAYER_LOCS[zone].pop(name)


if __name__ == "__main__":
    start_server = websockets.serve(update_loc, BIND_HOST, BIND_PORT)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
