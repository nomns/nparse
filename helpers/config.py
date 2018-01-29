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
    """ Return True if settings specific to nparse are valid, else False."""
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

    try:
        _ = int(data['general']['update_interval'])
    except:
        raise ValueError(
            'Critical Config Problem',
            'There are settings missing in the config file which should not be missing.  Replace nparse.config.yaml into the same directory as the executable.'
        )
