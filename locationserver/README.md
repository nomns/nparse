# Location Server for nParse



The location server runs on port: `8424`

Set your nParse `Setttings -> Sharing -> Sharing Hostname` to: `ws://localhost:8424` (You can replace `locahost` with your ip or domain name)

Running
========

Setup:

1. Create the directory where you would like nParse to be cloned to and then `cd` into the directory.
2. Clone the repository: `git clone https://github.com/nomns/nparse.git .`
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment: 
    - Windows: `.\venv\scripts\activate.bat`
    - Linux: `source .venv/bin/activate`
5. Install pip requirements: `pip install -r requirements.txt`

Usage:

1. Activate the virtual environment: 
    - Windows: `.\venv\scripts\activate.bat`
    - Linux: `source .venv/bin/activate`
2. Run nParse: `python location_server.py`

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