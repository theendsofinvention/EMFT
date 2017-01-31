import re
import tempfile
import os
import subprocess
import sys
from zipfile import ZipFile, ZipInfo, BadZipFile
from json import loads

from natsort.natsort import natsorted
from custom_logging import make_logger
from custom_path import Path

__version__ = None

if hasattr(sys, 'frozen'):
    __version__ = Path(sys.executable).get_win32_file_info().file_version
elif os.environ.get('APPVEYOR'):
    __version__ = loads(subprocess.check_output(
        [r'C:\ProgramData\chocolatey\bin\gitversion.exe']).decode().rstrip()).get('FullSemVer')
else:
    # This is a potential security breach, but I'm leaving it as is as it should only be running scripted
    __version__ = loads(subprocess.check_output(['gitversion']).decode().rstrip()).get('FullSemVer')

__guid__ = '4ae6dbb7-5b26-28c6-b797-2272f5a074f3'

__appname__ = 'TEMP'

logger = make_logger(__name__)

re_obj_start = re.compile(r'\s*(?P<key>\[?.*\]?) =$')
re_obj_start_par = re.compile(r'\s*\{$')
re_obj_end = re.compile(r'\s*\},? -- end of (?P<key>\[?.*\]?)$')
re_value = re.compile(r'\s*(?P<key>\[.*\]) = .*,$')
re_long_string_start = re.compile(r'\s*(?P<key>\[.*\]) = .*\\$')
re_long_string_cont = re.compile(r'\s*.*\\$')
re_long_string_end = re.compile(r'.*\",$')


class Group:
    def __init__(self, l, l2, parent):
        self.l = l
        self.l2 = l2
        self.l3 = None
        self.o = {}
        self.parent = parent
        if isinstance(self.parent, Group):
            self.parent.add_group(self)
        self.__long_string = None

    @property
    def name(self):
        return re_obj_start.match(self.l).group('key')

    def close(self, l):
        self.l3 = l

    @property
    def start(self):
        return '\n'.join([self.l, self.l2])

    @property
    def stop(self):
        return self.l3

    def add_value(self, l):
        # if self.__long_string is not None:
        #     self.__long_string['l'].append(l)
        #     self.o[self.__long_string['k']] = '\n'.join(self.__long_string['l'])
        #     self.__long_string = None
        value_k = re_value.match(l).group('key')
        self.o[value_k] = l

    def start_long_string(self, l):
        long_string_k = re_long_string_start.match(l).group('key')
        self.__long_string = {'k': long_string_k, 'l': [l]}

    def cont_long_string(self, l):
        if self.__long_string is None:
            raise ValueError('expected long string: {}'.format(l))
        self.__long_string['l'].append(l)

    def end_long_string(self, l):
        if self.__long_string is None:
            raise ValueError('expected long string: {}'.format(l))
        self.__long_string['l'].append(l)
        self.o[self.__long_string['k']] = '\n'.join(self.__long_string['l'])
        self.__long_string = None

    def add_group(self, group):
        self.o[group.name] = group

    def __str__(self):
        out = [self.start]
        for k in natsorted(self.o.keys()):
            v = self.o[k]
            if isinstance(v, Group):
                out.append(str(v))
            else:
                out.append(v)
        out.append(self.stop)
        return '\n'.join(out)


class Miz:
    def __init__(self, path_to_miz_file, temp_dir=None, remove_temp=True):
        self.miz_path = Path(path_to_miz_file)
        if not self.miz_path.exists():
            raise FileNotFoundError(os.path.abspath(path_to_miz_file))
        logger.debug('making new Mission object based on miz file: {}'.format(self.miz_path.abspath()))
        self.temp_dir_path = Path(temp_dir or tempfile.mkdtemp())
        logger.debug('temporary directory for this mission object: {}'.format(self.temp_dir_path))
        self.files_in_zip = []
        self.__unzipped = False
        self.__remove_temp = remove_temp

    def __enter__(self):
        logger.debug('unzipping MIZ file')
        self.unzip()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug('closing MIZ file')
        if exc_type:
            logger.exception('there were error with this mission, keeping temp dir at "{}" and re-raising'.format(
                self.temp_dir_path))
            print(exc_type, exc_val)
            return False
        else:
            if self.__remove_temp:
                self.remove_temp_dir()

    @property
    def is_unzipped(self):
        return self.__unzipped

    @property
    def l10n(self):
        return Path(self.temp_dir_path).joinpath('l10n', 'DEFAULT', 'dictionary')

    @property
    def mission(self):
        return Path(self.temp_dir_path).joinpath('mission')

    def unzip(self, force=False):
        """Extracts MIZ file into temp dir"""
        logger.debug('unzipping miz into temp dir: "{}" -> {}'.format(self.miz_path.abspath(), self.temp_dir_path.abspath()))
        with ZipFile(self.miz_path.abspath()) as zip_file:
            try:
                logger.debug('reading infolist')
                zip_content = zip_file.infolist()
                self.files_in_zip = [f.filename for f in zip_content]
                for item in zip_content:  # not using ZipFile.extractall() for security reasons
                    assert isinstance(item, ZipInfo)
                    logger.debug('unzipping item: {}'.format(item.filename))
                    try:
                        zip_file.extract(item, self.temp_dir_path)
                    except RuntimeError:
                        logger.exception('filed to extract: {}'.format(item.filename))
                        raise
            except BadZipFile:
                logger.exception('error extracting zip file: {}'.format(self.miz_path.abspath()))
                raise
            except:
                logger.exception('error while unzipping miz file: {}'.format(self.miz_path.abspath()))
                raise
        logger.debug('checking miz content')
        for miz_item in map(os.path.join, [self.temp_dir_path],
                            ['./mission', './options', './warehouses', './l10n/DEFAULT/dictionary',
                             './l10n/DEFAULT/mapResource']):
            if not Path(miz_item).exists():
                logger.error('missing file in miz: {}'.format(miz_item))
                raise FileNotFoundError(Path(miz_item).abspath())
        logger.debug('all files have been found, miz successfully unzipped')
        self.__unzipped = True

    def reorder_lua_tables(self):
        self.__reorder_lua_table(self.mission)
        self.__reorder_lua_table(self.l10n)

    @staticmethod
    def __reorder_lua_table(in_file: Path or str, out_file: Path or str = None):
        in_file = Path(in_file)
        out_file = Path(out_file) if out_file else Path(in_file)
        with open(in_file.abspath(), encoding='iso8859_15') as f:
            lines = f.readlines()
        start_length = len(lines)
        current_group = None
        while lines:
            line = _next(lines)
            if re_obj_start.match(line):
                current_group = Group(line, lines.pop(0).rstrip(), current_group)
            elif re_obj_end.match(line):
                current_group.close(line)
                if current_group.parent:
                    current_group = current_group.parent
            elif re_long_string_start.match(line):
                current_group.start_long_string(line)
            elif re_long_string_cont.match(line):
                current_group.cont_long_string(line)
            elif re_value.match(line):
                current_group.add_value(line)
            elif re_long_string_end.match(line):
                current_group.end_long_string(line)
            elif re_obj_start_par.match(line):
                pass
            else:
                raise ValueError('PARSING ERROR: ', line)
        with open(out_file.abspath(), encoding='iso8859_15', mode='w') as f:
            f.write(current_group.__str__())
        with open(out_file.abspath(), encoding='iso8859_15', mode='r') as f:
            if not start_length == len(f.readlines()):
                raise RuntimeError('there was an error during the re-ordering process')

    def wipe_temp_dir(self):
        """Removes all files & folders from temp_dir, wiping it clean"""
        files = []
        folders = []
        logger.debug('wiping temporary directory')
        for root, _folders, _files in os.walk(self.temp_dir_path.abspath(), topdown=False):
            for f in _folders:
                folders.append(os.path.join(root, f))
            for f in _files:
                files.append(os.path.join(root, f))
        logger.debug('removing files')
        for f in files:
            logger.debug('removing: {}'.format(f))
            try:
                os.remove(f)
            except:
                logger.exception('could not remove: {}'.format(f))
                raise
        logger.debug('removing folders')
        for f in folders:
            logger.debug('removing: {}'.format(f))
            try:
                os.rmdir(f)
            except:
                logger.exception('could not remove: {}'.format(f))
                raise

    def remove_temp_dir(self):
        """Deletes the temporary directory"""
        logger.debug('removing temporary directory: {}'.format(self.temp_dir_path))
        self.wipe_temp_dir()
        try:
            os.rmdir(self.temp_dir_path)
        except:
            logger.exception('could not remove: {}'.format(self.temp_dir_path))
            raise


def show_dict(d: dict):
    for k in d.keys():
        if isinstance(d[k], dict):
            print(d[k]['__start'])
            show_dict(d[k])
            # print(d[k]['__end'])
        else:
            print(d[k])


def _next(_lines):
    return _lines.pop(0).rstrip()


if __name__ == '__main__':
    miz_file = r'C:\Users\bob\Saved Games\DCS\Missions\132nd\TRMT_2.3.1.81.miz'
    with Miz(miz_file, './temp', remove_temp=False) as miz:
        miz.unzip()
        for f in miz.files_in_zip:
            print(f)
        miz.reorder_lua_tables()
    exit(0)
    # print(current_group)
