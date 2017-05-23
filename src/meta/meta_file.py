# coding=utf-8
import abc
import time
from collections import OrderedDict

from ruamel.yaml import load as yload, resolver, add_constructor, add_representer
from utils import make_logger, Path

from src.meta.meta import Meta

logger = make_logger(__name__)

_yaml_mapping = resolver.BaseResolver.DEFAULT_MAPPING_TAG


def odict_represent(dumper, data):
    return dumper.represent_dict(data.iteritems())


def odict_construct(loader, node):
    return OrderedDict(loader.construct_pairs(node))


add_representer(OrderedDict, odict_represent)
add_constructor(_yaml_mapping, odict_construct)


class MetaFile(Meta):

    @property
    @abc.abstractmethod
    def meta_header(self):
        """"""

    @property
    @abc.abstractmethod
    def meta_version(self):
        """"""

    @abc.abstractmethod
    def meta_version_upgrade(self, from_version):
        """"""

    def __init__(self, path: str or Path, init_dict: OrderedDict = None, auto_read=True, encrypted=False):

        Meta.__init__(self, init_dict)

        self.free = True
        self.encrypt = encrypted

        if isinstance(path, Path):
            pass

        elif isinstance(path, str):
            path = Path(path)

        else:
            raise TypeError('expected a Path or a str, got: {}'.format(type(path)))

        self._path = path

        if auto_read:
            self.read()

    def __delitem__(self, key, _write=False):
        super(MetaFile, self).__delitem__(key)

        if _write:
            self.write()

    def __setitem__(self, key, value, _write=False):
        super(MetaFile, self).__setitem__(key, value)

        if _write:
            self.write()

    def debug(self, txt: str):
        logger.debug('{}: {}'.format(self.path.abspath(), txt))

    def exception(self, txt: str):
        logger.debug('{}: {}'.format(self.path.abspath(), txt))

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, value: str or Path):

        if isinstance(value, Path):
            pass

        elif isinstance(value, str):
            value = Path(value)

        else:
            raise TypeError('expected Path or str, got: {}'.format(type(value)))

        self._path = value

    def read(self):

        self.wait_for_lock()

        meta_updated = False

        try:

            if self.path.exists():

                if self.path.getsize() == 0:
                    self.debug('{}: removing existing empty file: {}'.format(self.__class__.__name__, self.path))
                    self.path.remove()

                    return

                try:

                    if self.encrypt:
                        self.load(self.path.bytes())

                    else:
                        self.load(self.path.text(encoding='utf8'))

                except ValueError:
                    raise ValueError('{}: metadata file corrupted'.format(self.path.abspath()))

                else:
                    try:
                        if not self.data['meta_header'] == self.meta_header:
                            raise TypeError('meta header mismatch, expected: "{}", got: "{}" on file: {}'.format(
                                self.meta_header, self.data['meta_header'], self.path.abspath()
                            ))
                        else:
                            del self.data['meta_header']

                    except KeyError:
                        pass

                    meta_updated = False

                    while self.data['meta_version'] < self.meta_version:
                        current_version = self.data['meta_version']
                        next_version = self.data['meta_version'] + 1
                        logger.debug('upgrading meta from version "{}"'.format(current_version))

                        if not self.meta_version_upgrade(current_version):
                            raise RuntimeError('failed to upgrade metadata to version "{}"'.format(next_version))

                        else:
                            logger.debug('successfully upgraded meta to version "{}"'.format(next_version))
                            meta_updated = True

                        self.data['meta_version'] = next_version

        except OSError:
            self.exception('error while reading metadata file')

        finally:
            self.free = True
            if meta_updated:
                self.write()

    def write(self):
        # noinspection PyTypeChecker
        if len(self._data) == 0:
            raise ValueError('no data to write')

        self.wait_for_lock()
        self.data['meta_header'] = self.meta_header
        self.data['meta_version'] = self.meta_version

        try:

            if self.encrypt:
                self.path.write_bytes(self.dump())

            else:
                self.path.write_text(self.dump(), encoding='utf8')

        except OSError:
            self.exception('error while writing metadata to file')

        finally:
            self.free = True

    def wait_for_lock(self):
        i = 0

        while not self.free:
            time.sleep(0.1)
            i += 1

            if i == 10:
                self.debug('waiting for resource lock')
                i = 0

        self.free = False

    @staticmethod
    def read_header(path):

        path = Path(path)
        data = yload(path.text(encoding='utf8'))

        return data['header']


def read_meta_header(meta_file_path: Path or str):
    return MetaFile.read_header(meta_file_path)
