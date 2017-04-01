# coding=utf-8

from os import walk, listdir
from os.path import abspath, isdir, join, basename

from utils.custom_logging import make_logger

from src.global_ import ENCODING

LOGGER = make_logger('skins')

available_skins = {
    'A-10A': set(),
    'A-10C': set(),
    'F-15C': set(),
    'FW-190D9': set(),
    'ka-50': set(),
    'L-39ZA': set(),
    'mi-8mt': set(),
    'mig-29a': set(),
    'mig-29s': set(),
    'P-51D': set(),
    'su-25': set(),
    'su-25t': set(),
    'su-27': set(),
    'su-33': set(),
    'TF-51D': set(),
}


def gather_in_folders(list_of_folders):
    for folder in list_of_folders:
        folder = abspath(folder)
        LOGGER.debug('gathering skins in {}'.format(folder))
        for ac_dir in listdir(folder):
            ac_dir_path = join(folder, ac_dir)
            if ac_dir in available_skins.keys() and isdir(ac_dir_path):
                for root, folders, files in walk(ac_dir_path):
                    if 'description.lua' in files:
                        skin_dir = basename(root)
                        desc_lua_path = join(root, 'description.lua')
                        skin_name = None
                        try:
                            with open(desc_lua_path, encoding=ENCODING) as _f:
                                for l in _f.readlines():
                                    if l[:5] == 'name=':
                                        skin_name = l[5:].rstrip().strip('"')
                        except UnicodeDecodeError:
                            print('error reading {}'.format(desc_lua_path))
                        if skin_name is None:
                            skin_name = skin_dir
                        # skin = Skin(skin_name, ac_dir)
                        available_skins[ac_dir].add(skin_name)


def available_skins_for(ac_type):
    return sorted(available_skins[ac_type])


if __name__ == '__main__':
    make_logger()
    folders_to_scan = [r'D:\DCS World\Bazar\Liveries']
    gather_in_folders(folders_to_scan)
    print('\n'.join([str(skin) for skin in available_skins_for('A-10C')]))
