# coding=utf-8
import os
import re
import time
import tempfile
from zipfile import ZipFile, ZipInfo, BadZipFile

from natsort import natsorted

from src.utils.custom_logging import make_logger
from src.utils.custom_path import Path
from src.utils.progress import Progress
from src.ui.main_ui_interface import I

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
    def __init__(self, path_to_miz_file, temp_dir=None):
        self.miz_path = Path(path_to_miz_file)
        if not self.miz_path.exists():
            raise FileNotFoundError(os.path.abspath(path_to_miz_file))
        logger.debug('making new Mission object based on miz file: {}'.format(self.miz_path.abspath()))
        self.temp_dir_path = Path(temp_dir or tempfile.mkdtemp())
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
        logger.debug(
            'unzipping miz into temp dir: "{}" -> {}'.format(self.miz_path.abspath(), self.temp_dir_path.abspath()))
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
        I.show_log_tab()
        self.__reorder_lua_table(self.mission)
        self.__reorder_lua_table(self.l10n)

    @staticmethod
    def __reorder_lua_table(in_file: Path or str, out_file: Path or str = None):
        logger.debug('{} -> {}'.format(in_file, out_file))
        in_file = Path(in_file)
        out_file = Path(out_file) if out_file else Path(in_file)
        with open(in_file.abspath(), encoding='iso8859_15') as f:
            lines = f.readlines()
        start_length = len(lines)
        current_group = None
        Progress.start('Reordering lua table', len(lines))
        idx = 0
        t = time.time()
        # with click.progressbar(lines, label='Reordering: {}'.format(Path(in_file).name)) as _lines:
            # with click.progressbar(length=len(lines), label='Reordering {}'.format(in_file)) as bar:
        while lines:
            line = lines.pop(0).rstrip()
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
            idx += 1
            if time.time() - t > 0.1:
                Progress.set_value(idx)
                t = time.time()
                # bar.update(1)
        Progress.done()
        logger.info('writing results to: {}'.format(out_file.abspath()))
        with open(out_file.abspath(), encoding='iso8859_15', mode='w') as f:
            f.write(current_group.__str__())
            f.write('\n')
        with open(out_file.abspath(), encoding='iso8859_15', mode='r') as f:
            if not start_length == len(f.readlines()):
                out_file.remove()
                raise RuntimeError(
                    'count does not match; there was an error during the re-ordering process (output file has been deleted).')

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


def reorder_miz_file(miz_file, output_dir, remove_temp=True):
    with Miz(miz_file, output_dir) as miz:
        miz.reorder_lua_tables()
        if remove_temp:
            miz.remove_temp_dir()