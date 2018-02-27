import os
from shutil import copy


map_list = [v.strip() for (k, v) in [line.strip().split('=')
                                     for line in open('map_keys.ini').readlines()]]

for map_name in map_list:
    extensions = ['.txt', '_1.txt', '_2.txt', '_3.txt', '_4.txt', '_5.txt']
    maps = [
        os.path.join('map_files_new/', m) for m in [
            (map_name + e) for e in extensions
        ] if os.path.exists(os.path.join('map_files_new/', m))
    ]
    if not maps:
        print('no files for', map_name)
    else:
        for file_ in maps:
            copy(file_, 'map_files/')
