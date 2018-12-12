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

    try:
        with open(_filename, 'r+') as f:
            data = json.loads(f.read())
    except:
        # nparse.config.json does not exist, create blank data
        data = {}


def save():
    """
    Saves json to previously opened location.
    """
    global data
    global _filename
    with open(_filename, mode='w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))


def get_setting(setting, default, func=None):
    try:
        assert(type(setting) == type(default))
        if func:
            if not func(setting):
                return default
        return setting
    except:
        return default


def verify_settings():
    global data
    # verify nparse.config.json contains what it should and
    # set defaults if appropriate

    # general
    data['general'] = data.get('general', {})
    data['general']['eq_log_dir'] = get_setting(
        data['general'].get('eq_log_dir', ''),
        ''
    )
    data['general']['parser_opacity'] = get_setting(
        data['general'].get('parser_opacity', 80),
        80,
        lambda x: (x > 0 and x <= 100)
    )
    data['general']['qt_scale_factor'] = get_setting(
        data['general'].get('qt_scale_factor', 100),
        100,
        lambda x: (x >= 100 and x <= 300)
    )
    data['general']['update_check'] = get_setting(
        data['general'].get('update_check', True),
        True
    )

    # maps
    data['maps'] = data.get('maps', {})
    data['maps']['auto_follow'] = get_setting(
        data['maps'].get('auto_follow', True),
        True
    )
    data['maps']['closest_z_alpha'] = get_setting(
        data['maps'].get('closest_z_alpha', 20),
        20,
        lambda x: (x >= 1 and x <= 100)
    )
    data['maps']['current_z_alpha'] = get_setting(
        data['maps'].get('current_z_alpha', 100),
        100,
        lambda x: (x >= 1 and x <= 100)
    )
    data['maps']['geometry'] = get_setting(
        data['maps'].get('geometry', [100, 100, 400, 200]),
        [100, 100, 400, 200],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int) and
            isinstance(x[3], int)
        )
    )
    data['maps']['grid_line_width'] = get_setting(
        data['maps'].get('grid_line_width', 1),
        1,
        lambda x: (x >= 1 and x <= 10)
    )
    data['maps']['last_zone'] = get_setting(
        data['maps'].get('last_zone', ''),
        ''
    )
    data['maps']['line_width'] = get_setting(
        data['maps'].get('line_width', 1),
        1,
        lambda x: (x >= 1 and x <= 10)
    )
    data['maps']['other_z_alpha'] = get_setting(
        data['maps'].get('other_z_alpha', 10),
        10,
        lambda x: (x >= 1 and x <= 100)
    )
    data['maps']['scale'] = get_setting(
        data['maps'].get('scale', 0.07),
        0.07
    )
    data['maps']['show_grid'] = get_setting(
        data['maps'].get('show_grid', True),
        True
    )
    data['maps']['show_mouse_location'] = get_setting(
        data['maps'].get('show_mouse_location', True),
        True
    )
    data['maps']['show_poi'] = get_setting(
        data['maps'].get('show_poi', True),
        True
    )
    data['maps']['toggled'] = get_setting(
        data['maps'].get('toggled', True),
        True
    )
    data['maps']['use_z_layers'] = get_setting(
        data['maps'].get('use_z_layers', False),
        False
    )

    # spells
    data['spells'] = data.get('spells', {})
    data['spells']['casting_window_buffer'] = get_setting(
        data['spells'].get('casting_window_buffer', 1000),
        1000,
        lambda x: (x >= 1 and x <= 4000)
    )
    data['spells']['delay_self_buffs_on_zone'] = get_setting(
        data['spells'].get('delay_self_buffs_on_zone', True),
        True
    )
    data['spells']['geometry'] = get_setting(
        data['spells'].get('geometry', [550, 100, 200, 400]),
        [550, 100, 200, 400],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int) and
            isinstance(x[3], int)
        )
    )
    data['spells']['level'] = get_setting(
        data['spells'].get('level', 1),
        1,
        lambda x: (x >= 1 and x <= 65)
    )
    data['spells']['toggled'] = get_setting(
        data['spells'].get('toggled', True),
        True
    )
    data['spells']['use_casting_window'] = get_setting(
        data['spells'].get('use_casting_window', True),
        True
    )
    data['spells']['use_custom_triggers'] = get_setting(
        data['spells'].get('use_custom_triggers', True),
        True
    )
    data['spells']['use_secondary'] = get_setting(
        data['spells'].get('use_secondary', ["levitate"]),
        ["levitate"],
        lambda x: isinstance(x, list)
    )
    data['spells']['use_secondary_all'] = get_setting(
        data['spells'].get('use_secondary_all', False),
        False
    )


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
