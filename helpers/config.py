"""
General global settings setup to provide settings.data
"""
import os
from glob import glob
import json

data = {}
triggers = {}
CONFIG_FILE = ''
TRIGGER_FILE = ''


def load(config_file='nparse.config.json', trigger_file='nparse.triggers.json'):
    """
    Load json from file.

    If resulting json has 'location' declared, 'data' dict will be wiped and
    populated with the yaml at file location 'location'.
    """
    global data, triggers, CONFIG_FILE, TRIGGER_FILE
    CONFIG_FILE = config_file
    TRIGGER_FILE = trigger_file

    # load config file
    try:
        data = json.loads(open(CONFIG_FILE, 'r+').read())
    except:
        # nparse.config.json does not exist, create blank data
        data = {}

    # load trigger file
    try:
        triggers = json.loads(open(TRIGGER_FILE, 'r+').read())
    except:
        # nparse.triggers.json does not exist, create blank data
        triggers = {}


def save(save_data=True, save_triggers=True):
    """
    Saves json to previously opened location.
    """
    global data, CONFIG_FILE, triggers, TRIGGER_FILE
    try:
        if save_data:
            open(CONFIG_FILE, mode='w').write(json.dumps(data, indent=4, sort_keys=True))
        if save_triggers:
            open(TRIGGER_FILE, mode='w').write(json.dumps(triggers, indent=4, sort_keys=True))
    except:
        pass  # fail silent


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
    data['general']['sound_volume'] = get_setting(
        data['general'].get('sound_volume', 25),
        25
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
    data['spells']['use_secondary'] = get_setting(
        data['spells'].get('use_secondary', None),
        ["levitate", "malise", "malisement"],
        lambda x: isinstance(x, list)
    )
    data['spells']['use_secondary_all'] = get_setting(
        data['spells'].get('use_secondary_all', False),
        False
    )
    data['spells']['buff_bar_color'] = get_setting(
        data['spells'].get('buff_bar_color', [40, 122, 169]),
        [40, 122, 169],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )

    data['spells']['debuff_bar_color'] = get_setting(
        data['spells'].get('debuff_bar_color', [221, 119, 0]),
        [221, 119, 0],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )
    data['spells']['buff_text_color'] = get_setting(
        data['spells'].get('buff_text_color', [0, 0, 0]),
        [0, 0, 0],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )
    data['spells']['debuff_text_color'] = get_setting(
        data['spells'].get('debuff_text_color', [0, 0, 0]),
        [0, 0, 0],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )
    data['spells']['you_target_color'] = get_setting(
        data['spells'].get('you_target_color', [22, 66, 91]),
        [22, 66, 91],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )
    data['spells']['friendly_target_color'] = get_setting(
        data['spells'].get('friendly_target_color', [0, 68, 0]),
        [0, 68, 0],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )
    data['spells']['enemy_target_color'] = get_setting(
        data['spells'].get('enemy_target_color', [68, 0, 0]),
        [68, 0, 0],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )
    data['spells']['target_text_color'] = get_setting(
        data['spells'].get('target_text_color', [255, 255, 255]),
        [255, 255, 255],
        lambda x: (
            len(x) == 4 and
            isinstance(x[0], int) and
            isinstance(x[1], int) and
            isinstance(x[2], int)
        )
    )

    data['spells']['sound_file'] = get_setting(
        data['spells'].get('sound_file', 'data/mp3/ding.mp3'),
        'data/mp3/alert.mp3'
    )
    data['spells']['sound_enabled'] = get_setting(
        data['spells'].get('sound_enabled', True),
        True
    )

    # triggers
    data['triggers'] = data.get('triggers', {})
    data['triggers']['toggled'] = get_setting(
        data['triggers'].get('toggled', True),
        True
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
