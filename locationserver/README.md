# Location Server for nParse



The location server runs on port: `8424`

Set your nParse `Settings -> Sharing -> Sharing Hostname` to: `ws://localhost:8424` (You can replace `locahost` with your ip or domain name)

Running
========

Usage:

1. Install docker (Linux) or Docker Desktop (Windows/OSX).
2. To build and run in Docker, use one of these commands:
   1. docker-compose: `docker-compose up -d`
   2. docker:
      1. `docker build -q .`
      2. `docker run --rm  -d -p 8424:8424 --name nparse-locserver <image_sha>` (replacing `<image_sha>` with the output of the first command)

Development
========

You can use `python fake_loc_sender.py` to send random fake locations in west freeport.

Location Message Example:
```
message = {}
message["type"] = "location"
message["group_key"] = "public"
message["location"] = {}
message["location"]["zone"] = "west freeport"
message["location"]["player"] = "tester2"
message["location"]["x"] = -101.72,
message["location"]["y"] = -30.79,
message["location"]["z"] = -24.25,
message["location"]["timestamp"] = datetime.now().isoformat()
```
Waypoint Message Example:
```
message = {}
message["type"] = "waypoint"
message["group_key"] = "public"
message["location"] = {}
message["location"]["zone"] = "west freeport"
message["location"]["player"] = "tester2"
message["location"]["x"] = -101.72,
message["location"]["y"] = -30.79,
message["location"]["z"] = -24.25,
message["location"]["timestamp"] = datetime.now().isoformat()
message["location"]["icon"] = "corpse"
```