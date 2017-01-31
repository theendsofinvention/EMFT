import re
import tempfile
import os
import subprocess
import sys
from zipfile import ZipFile
from json import loads

from slpp import slpp
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


class Group:
    def __init__(self, l, l2, parent):
        self.l = l
        self.l2 = l2
        self.l3 = None
        self.o = {}
        self.parent = parent
        if isinstance(self.parent, Group):
            self.parent.add_group(self)

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
        value_k = re_value.match(l).group('key')
        self.o[value_k] = l

    def add_group(self, group):
        self.o[group.name] = group

    def __str__(self):
        out = [self.start]
        for k in sorted(self.o.keys()):
            v = self.o[k]
            # print(type(v))
            if isinstance(v, Group):
                out.append(str(v))
            else:
                out.append(v)
        # print(out)
        out.append(self.stop)
        return '\n'.join(out)


class Miz:
    def __init__(self, path_to_miz_file, temp_dir=None):
        self.miz_path = os.path.abspath(path_to_miz_file)
        if not os.path.exists(self.miz_path):
            raise FileNotFoundError(os.path.abspath(path_to_miz_file))
        logger.debug('making new Mission object based on miz file: {}'.format(self.miz_path))
        self.temp_dir_path = temp_dir or tempfile.mkdtemp()
        logger.debug('temporary directory for this mission object: {}'.format(self.temp_dir_path))
        self.files_in_zip = []
        self.__unzipped = False

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
            self.remove_temp_dir()

    @property
    def is_unzipped(self):
        return self.__unzipped

    @property
    def l10n(self):
        return Path(self.temp_dir_path).joinpath('l10n', 'DEFAULT', 'dictionary')

    @property
    def mission(self):
        return Path(self.temp_dir_path).joinpath('l10n', 'DEFAULT', 'mission')

    def decode(self):
        self.logger.debug('reading Mission files from disk')
        self.decode_ln10()
        self.decode_mission(self.ln10)

    def unzip(self, force=False):
        """Extracts MIZ file into temp dir"""
        self.logger.debug('unzipping miz into temp dir: "{}" -> {}'.format(self.miz_path, self.temp_dir_path))
        with ZipFile(self.miz_path) as zip_file:
            try:
                self.logger.debug('reading infolist')
                zip_content = zip_file.infolist()
                self.files_in_zip = [f.filename for f in zip_content]
                for item in zip_content:  # not using ZipFile.extractall() for security reasons
                    assert isinstance(item, ZipInfo)
                    self.logger.debug('unzipping item: {}'.format(item.filename))
                    try:
                        zip_file.extract(item, self.temp_dir_path)
                    except RuntimeError:
                        raise MizErrors.ExtractError(item)
            except BadZipFile:
                raise MizErrors.CorruptedMizError(self.miz_path)
            except:
                self.logger.exception('error while unzipping miz file: {}'.format(self.miz_path))
                raise
        self.logger.debug('checking miz content')
        for miz_item in map(join, [self.temp_dir_path],
                            ['./mission', './options', './warehouses', './l10n/DEFAULT/dictionary',
                             './l10n/DEFAULT/mapResource']):
            if not exists(miz_item):
                self.logger.error('missing file in miz: {}'.format(miz_item))
                raise MizErrors.MissingFileInMizError(miz_item)
        self.logger.debug('all files have been found, miz successfully unzipped')
        self.__unzipped = True

    def __encode_mission(self):
        self.logger.debug('writing mission dictionary to mission file: {}'.format(self.mission_file_path))
        parser = SLPP()
        try:
            self.logger.debug('encoding dictionary to lua table')
            raw_text = parser.encode(self.__mission.d)
        except:
            self.logger.exception('error while encoding')
            raise
        try:
            self.logger.debug('overwriting mission file')
            with open(self.mission_file_path, mode="w", encoding='iso8859_15') as _f:
                _f.write('mission = ')
                raw_text = re_sub(RE_SPACE_AFTER_EQUAL_SIGN, "= \n", raw_text)
                _f.write(raw_text)
        except:
            self.logger.exception('error while writing mission file: {}'.format(self.mission_file_path))
            raise

    def __encode_ln10(self):
        self.logger.debug('writing ln10 to: {}'.format(self.ln10_file_path))
        parser = SLPP()
        try:
            self.logger.debug('encoding dictionary to lua table')
            raw_text = parser.encode(self.ln10)
        except:
            self.logger.exception('error while encoding')
            raise
        try:
            self.logger.debug('overwriting mission file')
            with open(self.ln10_file_path, mode="w") as _f:
                _f.write('dictionary = ')
                raw_text = re_sub(RE_SPACE_AFTER_EQUAL_SIGN, "= \n", raw_text)
                _f.write(raw_text)
        except:
            self.logger.exception('error while writing ln10 file: {}'.format(self.ln10_file_path))
            raise

    def zip(self):
        self.__encode_mission()
        self.__encode_ln10()
        out_file = abspath('{}_ESME.miz'.format(self.miz_path[:-4])).replace('\\', '/')
        try:
            self.logger.debug('zipping mission into: {}'.format(out_file))
            with ZipFile(out_file, mode='w', compression=8) as _z:
                for f in self.files_in_zip:
                    full_path = abspath(join(self.temp_dir_path, f)).replace('\\', '/')
                    self.logger.debug("injecting in zip file: {}".format(full_path))
                    _z.write(full_path, arcname=f)
        except:
            self.logger.exception('error while zipping miz file')
            raise

    def wipe_temp_dir(self):
        """Removes all files & folders from temp_dir, wiping it clean"""
        files = []
        folders = []
        self.logger.debug('wiping temporary directory')
        for root, _folders, _files in walk(self.temp_dir_path, topdown=False):
            for f in _folders:
                folders.append(join(root, f))
            for f in _files:
                files.append(join(root, f))
        self.logger.debug('removing files')
        for f in files:
            self.logger.debug('removing: {}'.format(f))
            try:
                remove(f)
            except:
                self.logger.exception('could not remove: {}'.format(f))
                raise
        self.logger.debug('removing folders')
        for f in folders:
            self.logger.debug('removing: {}'.format(f))
            try:
                rmdir(f)
            except:
                self.logger.exception('could not remove: {}'.format(f))
                raise

    def remove_temp_dir(self):
        """Deletes the temporary directory"""
        self.logger.debug('removing temporary directory: {}'.format(self.temp_dir_path))
        self.wipe_temp_dir()
        try:
            rmdir(self.temp_dir_path)
        except:
            self.logger.exception('could not remove: {}'.format(self.temp_dir_path))
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


def obj(_line, _lines):
    _o = {}
    _k = re_obj_start.match(_line).group('key')
    _start = [_line]
    print('START', _k, '||', _line)
    _line = _next(_lines)
    assert re_obj_start_par.match(_line), _line
    _start.append(_line)
    _o['__start'] = '\n'.join(_start)
    while not '-- end of {}'.format(_k) in _line:
        _line = _next(_lines)
        print('uh', _line)
        if re_obj_start.match(line):
            _kk = re_obj_start.match(line).group('key')
            o[_kk] = obj(line, lines)

    return _o

class Value:

    def __init__(self, l):
        self.l = l


if __name__ == '__main__':
    # fp = r'C:\Users\bob\Saved Games\DCS\Missions\132nd\DEVEL\TRMT\l10n\DEFAULT\dictionary'
    fp = r'C:\Users\bob\Saved Games\DCS\Missions\132nd\DEVEL\TRMT\mission'
    op = r'C:\Users\bob\Saved Games\DCS\Missions\132nd\DEVEL\TRMT\mission3'
    parser = slpp.SLPP()
    with open(fp, encoding='iso8859_15') as f:
        lines = f.readlines()
    # assert lines.pop(0) == 'mission = \n'
    # assert lines.pop(0) == '{\n'
    # assert lines.pop() == '} -- end of mission\n'
    # o = {}
    # mission = Group(lines.pop(0), None)
    current_group = None
    while lines:
        line = _next(lines)
        if re_obj_start.match(line):
            current_group = Group(line, lines.pop(0).rstrip(), current_group)
            # k = re_obj_start.match(line).group('key')
            # o[k] = obj(line, lines)
        elif re_obj_end.match(line):
            current_group.close(line)
            if current_group.parent:
                current_group = current_group.parent
            # k = re_obj_end.match(line).group('key')
            # print('END', k, '||', line)
        elif re_value.match(line):
            current_group.add_value(line)
            # k = re_value.match(line).group('key')
            # print('VAL', k, '||', line)
        elif re_obj_start_par.match(line):
            pass
        else:
            raise ValueError(line)
    print(current_group.name)
    with open(op, encoding='iso8859_15', mode='w') as f:
        f.write(current_group.__str__())
    # print(current_group)
