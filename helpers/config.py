"""
General global settings setup to provide settings.data
"""
import yaml

data = {}
_filename = ''

def load(filename):
    """
    Load yaml from file.

    If resulting json has 'location' declared, 'data' dict will be wiped and
    populated with the yaml at file location 'location'.
    """
    global data
    global _filename
    _filename = filename

    with open(_filename) as f:
        data = yaml.load(f)

    if data and 'location' in data.keys():
        location = data['location']
        data = {}
        load(location)

def save():
    """
    Saves yaml file to previously opened location.
    """
    global data
    global _filename
    with open(_filename, mode='w') as f:
        f.write(yaml.dump(data, default_flow_style=False))

def verify_settings():
    return True
