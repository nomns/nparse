import asyncio
import datetime
import json
import ipaddress
import logging
import socket
import time

import websockets
from websockets import exceptions as ws_exc

logging.basicConfig()
LOG = logging.getLogger(__name__)

# Update these variables to change the listening interface/port.
BIND_HOST = "::"
BIND_PORT = 8424

PLAYERS = {}
PLAYER_LOCS = {}
WAYPOINT_LOCS = {}
LAST_SENT = {}


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


def location_event(group_key):
    waypoints = {}
    for zone in WAYPOINT_LOCS.get(group_key, {}):
        if zone not in waypoints:
            waypoints[zone] = {}
        for key, data in WAYPOINT_LOCS[group_key][zone].items():
            waypoints[zone][f"{key[0]}:{key[1]}"] = data

    return json.dumps(
        {"type": "state",
         "locations": PLAYER_LOCS.get(group_key, {}),
         "waypoints": waypoints})


def users_event():
    return json.dumps({"type": "users", "count": len(PLAYERS)})


def clean_old_waypoints():
    now = datetime.datetime.now().timestamp()
    for group_key in WAYPOINT_LOCS:
        for zone in WAYPOINT_LOCS[group_key]:
            for waypoint in list(WAYPOINT_LOCS[group_key][zone]):
                if now > waypoint[1]:
                    WAYPOINT_LOCS[group_key][zone].pop(waypoint)


async def notify_location(websocket, group_key):
    now = time.time()
    if now < LAST_SENT.get(group_key, 0) + 0.5:
        # print("Sending too fast.")
        return
    LAST_SENT[group_key] = now

    clean_old_waypoints()

    message = location_event(group_key)
    logging.warning("Notifying locations for %s: %s" % (group_key, message))
    if PLAYERS:
        keyed_players = [
            user for user in PLAYERS
            # if user != websocket and
            if PLAYERS[user][1] == group_key]
        if keyed_players:
            await asyncio.wait([user.send(message) for user in keyed_players])


async def notify_users(websocket):
    message = users_event()
    logging.warning("Notifying players: %s" % message)
    if PLAYERS and len(PLAYERS) > 1:
        await asyncio.wait([user.send(message) for user in PLAYERS
                            if user != websocket])


async def register(websocket, player_name=None, group_key=None):
    PLAYERS[websocket] = (player_name, group_key)
    logging.warning("Registering player: %s" % websocket.remote_address[0])
    # await notify_users(websocket)


async def unregister(websocket):
    player_name, group_key = PLAYERS.pop(websocket)
    if player_name:
        await remove_player_from_zones(player_name, group_key)
    logging.warning("Deregistering player: %s" % websocket.remote_address[0])
    # await notify_users(websocket)


async def update_data_for_player(websocket, data, group_key):
    zone_name = data.pop('zone', 'unknown').lower()
    player_name = data.pop('player', 'unknown').capitalize()
    if group_key not in PLAYER_LOCS:
        PLAYER_LOCS[group_key] = {}
    if zone_name not in PLAYER_LOCS[group_key]:
        PLAYER_LOCS[group_key][zone_name] = {}
    await remove_player_from_zones(player_name, group_key=group_key,
                                   except_zone=zone_name)
    PLAYERS[websocket] = (player_name, group_key)
    PLAYER_LOCS[group_key][zone_name][player_name] = data


async def update_data_for_waypoint(websocket, data, group_key):
    zone_name = data.pop('zone', 'unknown').lower()
    player_name = data.pop('player', 'unknown').capitalize()
    try:
        timeout = int(data.pop('timeout'))
    except (TypeError, KeyError):
        timeout = 60
    expiry = (datetime.datetime.now() + datetime.timedelta(minutes=timeout)).timestamp()
    if group_key not in WAYPOINT_LOCS:
        WAYPOINT_LOCS[group_key] = {}
    if zone_name not in WAYPOINT_LOCS[group_key]:
        WAYPOINT_LOCS[group_key][zone_name] = {}
    PLAYERS[websocket] = (player_name, group_key)
    WAYPOINT_LOCS[group_key][zone_name][(player_name, expiry)] = data


async def remove_player_from_zones(name, group_key, except_zone=None):
    for zone in list(PLAYER_LOCS[group_key]):
        if zone == except_zone:
            continue
        if name in PLAYER_LOCS[group_key][zone]:
            PLAYER_LOCS[group_key][zone].pop(name)
            if len(PLAYER_LOCS[group_key][zone]) == 0:
                PLAYER_LOCS[group_key].pop(zone)
                if len(PLAYER_LOCS[group_key]) == 0:
                    PLAYER_LOCS.pop(group_key)


async def update_loc(websocket, path):
    await register(websocket)
    try:
        # await notify_location(websocket)
        async for message in websocket:
            data = json.loads(message)
            group_key = data.pop('group_key', 'public')
            if data['type'] == "location":
                data = data['location']
                await update_data_for_player(websocket, data, group_key=group_key)
                await notify_location(websocket, group_key)
            elif data['type'] == "waypoint":
                data = data['location']
                await update_data_for_waypoint(websocket, data, group_key=group_key)
                await notify_location(websocket, group_key)
    except ws_exc.ConnectionClosedError:
        logging.warning(
            "Player disconnected: %s" % websocket.remote_address[0])
    finally:
        await unregister(websocket)


if __name__ == "__main__":
    sock_family = socket.AF_INET6
    if ipaddress.ip_address(BIND_HOST).version == 4:
        sock_family = socket.AF_INET
    sock = socket.socket(sock_family, socket.SOCK_STREAM)
    sock.bind((BIND_HOST, BIND_PORT))

    start_server = websockets.serve(update_loc, sock=sock)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
