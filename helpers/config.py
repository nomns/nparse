"""
General global settings setup to provide settings.data
"""
import os
from glob import glob
import json

data = {}
_filename = ''


def load(filename):
    """
    Load json from file.

    If resulting json has 'location' declared, 'data' dict will be wiped and
    populated with the yaml at file location 'location'.
    """
    global data
    global _filename
    _filename = filename

    with open(_filename) as f:
        data = json.loads(f.read())

    if data and 'location' in data.keys():
        location = data['location']
        data = {}
        load(location)


def save():
    """
    Saves json to previously opened location.
    """
    global data
    global _filename
    with open(_filename, mode='w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))


def verify_settings():
    global data
    # verify nparse.config.json contains what it should
    try:
        # general
        _ = int(data['general']['parser_opacity'])
        assert((_ > 0 and _ <= 100))

        # maps
        _ = int(data['maps']['grid_line_width'])
        _ = int(data['maps']['scale'])
        _ = bool(data['maps']['show_poi'])
        _ = bool(data['maps']['toggled'])
        _ = bool(data['maps']['auto_follow'])
        geometry = data['maps'].get('geometry', None)
        if geometry:
            assert(len([int(x) for x in geometry]) == 4)

        # spells
        _ = int(data['spells']['level'])
        assert(_ > 0 and _ <= 65)
        _ = int(data['spells']['casting_window_buffer'])
        _ = bool(data['spells']['use_casting_window'])
        _ = bool(data['spells']['use_secondary_all'])
        _ = bool(data['spells']['delay_self_buffs_on_zone'])
        _ = bool(data['spells']['toggled'])
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
