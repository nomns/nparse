import os
from glob import glob
from typing import List


def get_profiles() -> List[str]:
    #  remove '.json' from end of file
    return [os.path.basename(f[:-5]) for f in glob("data/profiles/*.json")]
