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


import os
from glob import glob


def verify_settings():
    global data
    # verify nparse.config.yaml contains what it should
    try:
        # general
        _ = int(data['general']['update_interval_msec'])

        # maps
        _ = int(data['maps']['grid_line_width'])
        _ = int(data['maps']['scale'])
        _ = (type(data['maps']['show_poi']) == bool)
        _ = (type(data['maps']['toggled']) == bool)
        geometry = data['maps'].get('geometry', None)
        if geometry:
            assert(len([int(x) for x in geometry]) == 4)

        # spells
        _ = int(data['spells']['level'])
        _ = int(data['spells']['seconds_offset'])
        _ = (type(data['spells']['toggled']) == bool)
        geometry = data['spells'].get('geometry', None)
        if geometry:
            assert(len([int(x) for x in geometry]) == 4)

    except:
        raise ValueError('critical')


def verify_paths():
    global data
    # verify eq log directory exists
    try:
        assert(os.path.isdir(os.path.join(data['general']['eq_log_dir'])))
    except:
        raise ValueError(
            'Everquest Log Directory Error',
            'Everquest log directory needs to be set before proceeding.  Use systemtray icon menu to set.'
        )

    # verify eq log directory contains log files for reading.
    log_filter = os.path.join(data['general']['eq_log_dir'], 'eqlog*.*')
    if not glob(log_filter):
        raise ValueError(
            'No Logs Found',
            'No Everquest log files were found.  Ensure both your directory is set and logging is turned on in your Everquest client.'
        )
