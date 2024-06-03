from datetime import datetime
import json

from PySide6.QtCore import QObject, QUrl, Signal, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtWebSockets import QWebSocket

from nParse.helpers import config, to_real_xy
from nParse.parsers.maps.mapclasses import MapPoint

class LocationSharingSignals(QObject):
    textMessageReceived = Signal(str)

class LocationSharingService(QObject):
    character_name = None
    group_key = None
    host = None
    running = False
    websocket = None
    zone_name = None
    x = 0
    y = 0
    z = 0

    def __init__(self):
        super().__init__()

        # Connect self.config_updated to the settings signals
        QApplication.instance()._signals["settings"].config_updated.connect(self.config_updated)

        # Set self.character_name from config
        self.character_name = config.data["sharing"]["player_name"]

        # Set self.group_key - Handle settings changes and account for discord override
        if config.data["sharing"]["discord_channel"]:
            key = config.data["discord"]["url"].split("?")[0].split("/")[-1]
            if key != "" and self.group_key != key:
                self.group_key = key
        else:
            self.group_key = config.data["sharing"]["group_key"]
        
        # Set self.host from config
        self.host = config.data["sharing"]["url"]

        # Set self.zone_name from config
        self.zone_name = config.data["maps"]["last_zone"]

        # Start the service from init if sharing is enabled in the config
        if config.data.get("sharing", {}).get("enabled", False):
            self.start()

    # Used to start the websocket service and connect signals
    def start(self):
        # Setup Websocket
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.websocket_connected)
        self.websocket.error.connect(self.websocket_error)
        self.websocket.disconnected.connect(self.websocket_disconnected)
        self.websocket.textMessageReceived.connect(self.websocket_message)
        self.websocket.open(QUrl(self.host))

        # Setup signals
        QApplication.instance().aboutToQuit.connect(self.stop)
        QApplication.instance()._signals["logreader"].character_updated.connect(self.character_updated)
        QApplication.instance()._signals["maps"].new_zone.connect(self.zone_updated)
        QApplication.instance()._signals["maps"].location.connect(self.share_location)
        QApplication.instance()._signals["maps"].death.connect(self.share_death)
        QApplication.instance()._signals["locationsharing"].textMessageReceived.connect(self.parse)

        # Set self.running to true
        self.running = True

    # Used to stop the websocket service and disconnect signals
    def stop(self):
        # Shutdown the websocket if it exists
        if self.websocket:
            self.websocket.close()
            self.websocket = None

        # Disconnect signals
        QApplication.instance().aboutToQuit.disconnect(self.stop)
        QApplication.instance()._signals["logreader"].character_updated.disconnect(self.character_updated)
        QApplication.instance()._signals["maps"].new_zone.disconnect(self.zone_updated)
        QApplication.instance()._signals["maps"].location.disconnect(self.share_location)
        QApplication.instance()._signals["maps"].death.disconnect(self.share_death)
        QApplication.instance()._signals["locationsharing"].textMessageReceived.disconnect(self.parse)

        # Set self.running to false
        self.running = False

    def config_updated(self):
        # Handle performing character name override when saving a new name from settings
        # Use Override Name if sharing is anabled
        if (
            config.data["sharing"]["enabled"]
            and config.data["sharing"]["player_name_override"]
        ):
            self.character_name = config.data["sharing"]["player_name"]
        # Use the name from the logreader if available
        elif QApplication.instance()._log_reader and QApplication.instance()._log_reader.character_name:
            self.character_name = QApplication.instance()._log_reader.character_name
            # Update config so if the user starts up and has not zoned, we use the correct name
            if config.data["sharing"]["player_name"] != self.character_name:
                config.data["sharing"]["player_name"] = self.character_name
                config.save()
        # Set the name to the last used name in player sharing if all else fails
        else:
            self.character_name = config.data["sharing"]["player_name"]

        # Handle setting groupkey from settings changes and account for discord override
        if config.data["sharing"]["discord_channel"]:
            key = config.data["discord"]["url"].split("?")[0].split("/")[-1]
            if key != "" and self.group_key != key:
                self.group_key = key
        else:
            if self.group_key != config.data["sharing"]["group_key"]:
                self.group_key = config.data["sharing"]["group_key"]

        # Start the sharing service if it is not already running
        if config.data["sharing"]["enabled"] == True and self.running == False:
            self.start()

        # Stop the sharing srevice if it is currently running
        if config.data["sharing"]["enabled"] == False and self.running == True:
            self.stop()

    # Handle character updates from the log reader signal
    def character_updated(self, character_name):
        # Only update the character_name if player_name_override is not true in config sharing
        if not config.data["sharing"]["player_name_override"]:
            self.character_name = character_name
            if config.data["sharing"]["player_name"] != self.character_name:
                config.data["sharing"]["player_name"] = self.character_name
                config.save()

    def zone_updated(self, zone_name):
        self.zone_name = zone_name

    # Websocket Connected - This can be useful for delaying a send until the connection is actually connected.
    def websocket_connected(self):
        self.websocket.ping()
        print("Connected")

    # Websocket Error
    def websocket_error(self, message):
        pass
    
    # Websocket Discconected
    def websocket_disconnected(self):
        if config.data.get("sharing", {}).get("enabled", False):
            reconnect_delay  = int(config.data.get("sharing", {}).get("reconnect_delay", 5) * 1000)
            _ = QTimer().singleShot(reconnect_delay , self.websocket_reconnect )

    # Websocket reconnect logic
    def websocket_reconnect(self):
        if config.data.get("sharing", {}).get("enabled", False):
            self.websocket.open(QUrl(self.host))

    # Websocket message handler - handles any incoming messages from the websocket server
    def websocket_message(self, message):
        QApplication.instance()._signals["locationsharing"].textMessageReceived.emit(message)
        print(message)

    # Parses messages from the websocket server
    def parse(self, websocket_message):
        message = json.loads(websocket_message)
        if message["type"] == "state":
            # Only process locations if there is data for our location
            if message.get("locations", {}).get(self.zone_name.lower(), False):
                # Interate through players in the zone
                for player in message["locations"][self.zone_name.lower()]:
                    #Process any players that are not us
                    if player.lower() != self.character_name.lower():
                        p_data = message["locations"][self.zone_name.lower()][player]
                        p_timestamp = datetime.fromisoformat(str(p_data["timestamp"]))
                        p_point = MapPoint(x=int(p_data["x"]), y=int(p_data["y"]), z=int(p_data["z"]))
                        #Add the player map point to the map
                        QApplication.instance()._parsers_dict["maps"]._map.add_player(player, p_timestamp, p_point)

                # Remove players that aren't in the zone
                players_to_remove = []
                # Check players in the currently loaded QT map
                for player in QApplication.instance()._parsers_dict["maps"]._map._data.players:
                    # if the player is no longre in the zone and not ourselves, append them to be removed
                    if player not in message["locations"][self.zone_name.lower()] and player != "__you__":
                        players_to_remove.append(player)
                for player in players_to_remove:
                    QApplication.instance()._parsers_dict["maps"]._map.remove_player(player)

            # Only process waypoints if there is data for our location
            if message.get("waypoints", {}).get(self.zone_name.lower(), False):
                # Iterate through the waypoints in the zone
                for waypoint in message["waypoints"][self.zone_name.lower()]:
                    w_data = message["waypoints"][self.zone_name.lower()][waypoint]
                    w_point = MapPoint(x=int(w_data["x"]), y=int(w_data["y"]), z=int(w_data["z"]))
                    w_icon = w_data.get("icon", "corpse")
                    QApplication.instance()._parsers_dict["maps"]._map.add_waypoint(waypoint, w_point, w_icon)

            # Remove waypoints that aren't in the zone
            waypoints_to_remove = []
            for waypoint in QApplication.instance()._parsers_dict["maps"]._map._data.waypoints:
                if waypoint not in message["waypoints"][self.zone_name.lower()]:
                    waypoints_to_remove.append(waypoint)
            for waypoint in waypoints_to_remove:
                QApplication.instance()._parsers_dict["maps"]._map.remove_waypoint(waypoint)

    # Shares player location with the websocket server
    def share_location(self, timestamp_string, xyz_string):
        # Update self x y z
        self.x, self.y, self.z = [float(value) for value in xyz_string.strip().split(",")]

        # Convert x y values
        x, y = to_real_xy(self.x, self.y)

        # Construct the payload
        share_payload = {
            "x": x,
            "y": y,
            "z": self.z,
            "zone": self.zone_name,
            "player": self.character_name,
            "timestamp": timestamp_string
        }

        # Construct the message frame
        message = {"type": "location",
                "group_key": self.group_key,
                "location": share_payload}

        # Send the message
        print("Sending: %s" % message)
        self.websocket.sendTextMessage(json.dumps(message))

        # Below is an example of sending a fake message to verify both adding and removing entries works in field of bone at the cab gates
        # fakemessage = {}
        # fakemessage["type"] = "state"
        # fakemessage["locations"] = {'field of bone': {'ConfigureYou': {'x': -3535.0, 'y': 2735.0, 'z': 7.85, 'timestamp': datetime.now().isoformat(), 'icon': 'corpse'}}}
        # fakemessage["waypoints"] = {'field of bone': {'ConfigureYou': {'x': -3530.0, 'y': 2735.0, 'z': 7.85, 'timestamp': datetime.now().isoformat(), 'icon': 'corpse'}}}
        # self.websocket_message(json.dumps(fakemessage))

    # Shares player death with the websocket server
    def share_death(self, timestamp_string, log_string):
        # Convert x y values
        x, y = to_real_xy(self.x, self.y)

        # If the current player is in the zone construct and send the death message to the websocket server
        if "__you__" in QApplication.instance()._parsers_dict["maps"]._map._data.players:
            # Construct the payload
            share_payload = {
                "x": x,
                "y": y,
                "z": self.z,
                "zone": self.zone_name,
                "player": self.character_name,
                "timestamp": timestamp_string,
                "timeout": 60,
                "icon": "corpse"
            }

            # Construct the message frame
            message = {"type": "waypoint",
                "group_key": self.group_key,
                "location": share_payload}

            # Send the message
            self.websocket.sendTextMessage(json.dumps(message))