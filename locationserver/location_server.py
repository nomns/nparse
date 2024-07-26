import asyncio
import datetime
import json
import logging
import time

import websockets
import websockets.server
from websockets import exceptions as ws_exc

# Update this variable to change the listening port
BIND_PORT = 8424

# DO NOT EDIT BEYOND THIS LINE
logging.basicConfig()
LOG = logging.getLogger(__name__)

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


def location_event(group_key, zone_name):
    waypoints = {}
    for zone in WAYPOINT_LOCS.get(group_key, {}):
        # temporarily short-circuit and only send waypoints for the current zone
        if zone != zone_name:
            continue
        if zone not in waypoints:
            waypoints[zone] = {}
        for key, data in WAYPOINT_LOCS[group_key][zone].items():
            waypoints[zone][f"{key[0]}:{key[1]}"] = data

    return (
        {"type": "state",
         "locations": {zone_name: PLAYER_LOCS.get(group_key, {}).get(zone_name, {})},
         "waypoints": waypoints})


def users_event():
    return json.dumps({"type": "users", "count": len(PLAYERS)})


def clean_old_waypoints():
    now = datetime.datetime.now().timestamp()
    for group_key in list(WAYPOINT_LOCS):
        for zone in list(WAYPOINT_LOCS[group_key]):
            for waypoint in list(WAYPOINT_LOCS[group_key][zone]):
                if now > waypoint[1]:
                    WAYPOINT_LOCS[group_key][zone].pop(waypoint)
                    if not WAYPOINT_LOCS[group_key][zone]:
                        WAYPOINT_LOCS[group_key].pop(zone)
        if not WAYPOINT_LOCS[group_key]:
            WAYPOINT_LOCS.pop(group_key)


async def notify_location(websocket, group_key, zone_name):
    if group_key not in LAST_SENT:
        LAST_SENT[group_key] = {}
    now = time.time()
    if now < LAST_SENT[group_key].get(zone_name, 0) + 1:
        # print("Sending too fast.")
        return
    LAST_SENT[group_key][zone_name] = now

    clean_old_waypoints()

    loc_event = location_event(group_key, zone_name)
    message = json.dumps(loc_event)
    logging.warning("Notifying locations for %s (%s): %s" % (group_key, zone_name, message))
    if PLAYERS:
        keyed_players = [
            user for user in PLAYERS
            # if user != websocket and
            if PLAYERS[user][1] == group_key]
        if keyed_players:
            websockets.broadcast(keyed_players, message)


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
    if player_name or player_name == "":
        await remove_player_from_zones(player_name, group_key)
    logging.warning("Deregistering player: %s" % websocket.remote_address[0])
    # await notify_users(websocket)


async def update_data_for_player(websocket, data, group_key):
    zone_name = data.pop('zone', 'unknown').lower()
    player_name = data.pop('player', 'unknown').capitalize()

    old_player_name = PLAYERS[websocket][0]
    old_group_key = PLAYERS[websocket][1]
    # If the player name or group key changed, we need to clear out the old player from all zones
    # Otherwise, remove the player from all zones besides the current one
    if old_player_name != player_name or old_group_key != group_key:
        await remove_player_from_zones(old_player_name, group_key=old_group_key)
    else:
        await remove_player_from_zones(player_name, group_key=group_key,
                                       except_zone=zone_name)

    if group_key not in PLAYER_LOCS:
        PLAYER_LOCS[group_key] = {}
    if zone_name not in PLAYER_LOCS[group_key]:
        PLAYER_LOCS[group_key][zone_name] = {}

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
    for zone in list(PLAYER_LOCS.get(group_key, {})):
        if zone == except_zone:
            continue
        if name in PLAYER_LOCS[group_key][zone]:
            PLAYER_LOCS[group_key][zone].pop(name)
            if not PLAYER_LOCS[group_key][zone]:
                PLAYER_LOCS[group_key].pop(zone)
                if not PLAYER_LOCS[group_key]:
                    PLAYER_LOCS.pop(group_key)


async def update_loc(websocket: websockets.WebSocketServerProtocol):
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            group_key = data.pop('group_key', 'public')
            if data['type'] == "location":
                data = data['location']
                zone_name = data.get('zone', 'unknown').lower()
                await update_data_for_player(websocket, data, group_key=group_key)
                await notify_location(websocket, group_key, zone_name)
            elif data['type'] == "waypoint":
                data = data['location']
                zone_name = data.get('zone', 'unknown').lower()
                await update_data_for_waypoint(websocket, data, group_key=group_key)
                await notify_location(websocket, group_key, zone_name)
    except ws_exc.ConnectionClosedError:
        logging.warning(
            "Player disconnected: %s" % websocket.remote_address[0])
    finally:
        await unregister(websocket)


async def main():
    logging.warning("Starting asyncio loop...")
    async with websockets.server.serve(update_loc, port=BIND_PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
