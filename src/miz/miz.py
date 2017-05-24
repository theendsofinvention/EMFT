# coding=utf-8
import tempfile
from filecmp import dircmp
from os.path import exists, join
from zipfile import ZipFile, BadZipFile, ZipInfo

from sltp import SLTP
from utils import make_logger, Path, Progress

from src.dummy_miz import dummy_miz
from src.global_ import ENCODING
from src.miz.mission import Mission

logger = make_logger('miz')


# noinspection PyAbstractClass
class MizPath(Path):
    def __init__(self, path):
        Path.__init__(self, path)

        if not self.exists():
            raise FileNotFoundError(path)

        if not self.isfile():
            raise TypeError(path)

        if not self.ext == '.miz':
            raise ValueError(path)


class Miz:
    def __init__(self, path_to_miz_file, temp_dir=None, keep_temp_dir: bool = False):

        self.miz_path = Path(path_to_miz_file)

        if not self.miz_path.exists():
            raise FileNotFoundError(path_to_miz_file)

        if not self.miz_path.isfile():
            raise TypeError(path_to_miz_file)

        if not self.miz_path.ext == '.miz':
            raise ValueError(path_to_miz_file)

        if temp_dir is not None:
            raise PendingDeprecationWarning()

        self.keep_temp_dir = keep_temp_dir

        self.tmpdir = Path(tempfile.mkdtemp('EMFT_'))
        logger.debug('temporary directory: {}'.format(self.tmpdir.abspath()))

        self.zip_content = None
        self._mission = None
        self._mission_qual = None
        self._l10n = None
        self._l10n_qual = None
        self._map_res = None
        self._map_res_qual = None

    def __enter__(self):
        logger.debug('instantiating new Mission object as a context')
        self.unzip()
        self._decode()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error('there were error with this mission, keeping temp dir at "{}" and re-raising'.format(
                self.tmpdir.abspath()))
            logger.error('{}\n{}'.format(exc_type, exc_val))
            return False
        else:
            logger.debug('closing Mission object context')
            if not self.keep_temp_dir:
                logger.debug('removing temp dir: {}'.format(self.tmpdir.abspath()))
                self.tmpdir.rmtree()

    @property
    def mission_file(self):
        return self.tmpdir.joinpath('mission')

    @property
    def dictionary_file(self):
        return self.tmpdir.joinpath('l10n', 'DEFAULT', 'dictionary')

    @property
    def map_res_file(self):
        return self.tmpdir.joinpath('l10n', 'DEFAULT', 'mapResource')

    @property
    def mission(self) -> Mission:
        if self._mission is None:
            raise RuntimeError()
        return self._mission

    @property
    def l10n(self) -> dict:
        if self._l10n is None:
            raise RuntimeError()
        return self._l10n

    @property
    def map_res(self) -> dict:
        if self._map_res is None:
            raise RuntimeError()
        return self._map_res

    @staticmethod
    def reorder(miz_file_path, target_dir, skip_options_file):

        logger.info('re-ordering miz file: {}'.format(miz_file_path))
        logger.debug('destination folder: {}'.format(target_dir))
        logger.debug('{}option file'.format('skipping' if skip_options_file else 'including'))

        with Miz(miz_file_path) as m:

            def mirror_dir(src, dst):
                logger.debug('{} -> {}'.format(src, dst))
                diff_ = dircmp(src, dst, ignore)
                diff_list = diff_.left_only + diff_.diff_files
                logger.debug('differences: {}'.format(diff_list))
                for x in diff_list:
                    source = Path(diff_.left).joinpath(x)
                    target = Path(diff_.right).joinpath(x)
                    logger.debug('looking at: {}'.format(x))
                    if source.isdir():
                        logger.debug('isdir: {}'.format(x))
                        if not target.exists():
                            logger.debug('creating: {}'.format(x))
                            target.mkdir()
                        mirror_dir(source, target)
                    else:
                        logger.debug('copying: {}'.format(x))
                        source.copy2(diff_.right)
                for sub in diff_.subdirs.values():
                    assert isinstance(sub, dircmp)
                    mirror_dir(sub.left, sub.right)

            m.unzip(overwrite=True)
            m._decode()
            m._encode()

            if skip_options_file:
                ignore = ['options']
            else:
                ignore = []

            mirror_dir(m.tmpdir, target_dir)

    def _decode(self):

        logger.info('decoding lua tables')

        if not self.zip_content:
            self.unzip(overwrite=False)

        Progress.start('Decoding MIZ file', length=3)

        Progress.set_label('Decoding map resource')
        logger.debug('reading map resource file')
        with open(self.map_res_file, encoding=ENCODING) as f:
            self._map_res, self._map_res_qual = SLTP().decode(f.read())
        Progress.set_value(1)

        Progress.set_label('Decoding dictionary file')
        logger.debug('reading l10n file')
        with open(self.dictionary_file, encoding=ENCODING) as f:
            self._l10n, self._l10n_qual = SLTP().decode(f.read())
        Progress.set_value(2)

        Progress.set_label('Decoding mission file')
        logger.debug('reading mission file')
        with open(self.mission_file, encoding=ENCODING) as f:
            mission_data, self._mission_qual = SLTP().decode(f.read())
            self._mission = Mission(mission_data, self._l10n)
        Progress.set_value(3)

        logger.info('decoding done')

    def _encode(self):

        logger.info('encoding lua tables')

        Progress.start('Decoding MIZ file', length=3)

        Progress.set_label('Encoding map resource')
        logger.debug('encoding map resource')
        with open(self.map_res_file, mode='w', encoding=ENCODING) as f:
            f.write(SLTP().encode(self._map_res, self._map_res_qual))
        Progress.set_value(1)

        Progress.set_label('Encoding map resource')
        logger.debug('encoding l10n dictionary')
        with open(self.dictionary_file, mode='w', encoding=ENCODING) as f:
            f.write(SLTP().encode(self.l10n, self._l10n_qual))
        Progress.set_value(2)

        Progress.set_label('Encoding map resource')
        logger.debug('encoding mission dictionary')
        with open(self.mission_file, mode='w', encoding=ENCODING) as f:
            f.write(SLTP().encode(self.mission.d, self._mission_qual))
        Progress.set_value(3)

        logger.info('encoding done')

    def unzip(self, overwrite: bool = False):

        if self.zip_content and not overwrite:
            raise FileExistsError(self.tmpdir.abspath())

        logger.debug('unzipping miz to temp dir')

        try:

            with ZipFile(self.miz_path.abspath()) as zip_file:

                logger.debug('reading infolist')

                self.zip_content = [f.filename for f in zip_file.infolist()]

                for item in zip_file.infolist():  # not using ZipFile.extractall() for security reasons
                    assert isinstance(item, ZipInfo)

                    logger.debug('unzipping item: {}'.format(item))

                    try:
                        zip_file.extract(item, self.tmpdir.abspath())
                    except:
                        logger.error('failed to extract archive member: {}'.format(item))
                        raise

        except BadZipFile:
            raise BadZipFile(self.miz_path.abspath())

        except:
            logger.exception('error while unzipping miz file: {}'.format(self.miz_path.abspath()))
            raise

        logger.debug('checking miz content')

        # noinspection PyTypeChecker
        for miz_item in map(
                join,
                [self.tmpdir.abspath()],
                [
                    'mission',
                    'options',
                    'warehouses',
                    'l10n/DEFAULT/dictionary',
                    'l10n/DEFAULT/mapResource'
                ]):

            if not exists(miz_item):
                logger.error('missing file in miz: {}'.format(miz_item))
                raise FileNotFoundError(miz_item)

        for filename in self.zip_content:
            p = self.tmpdir.joinpath(filename)
            if not p.exists():
                raise FileNotFoundError(p.abspath())

        logger.debug('all files have been found, miz successfully unzipped')

    def zip(self, destination=None):

        self._encode()

        if destination is None:
            destination = Path(self.miz_path.dirname()).joinpath('{}_EMFT.miz'.format(self.miz_path.namebase))

        destination = Path(destination).abspath()

        logger.debug('zipping mission to: {}'.format(destination))

        with open(destination, mode='wb') as f:
            f.write(dummy_miz)

        with ZipFile(destination, mode='w', compression=8) as _z:

            for f in self.zip_content:
                abs_path = self.tmpdir.joinpath(f).abspath()
                logger.debug('injecting in zip file: {}'.format(abs_path))
                _z.write(abs_path, arcname=f)

        return destination
