# coding=utf-8
import time
import abc
from collections import OrderedDict

from ruamel.yaml import dump as ydump, load as yload, RoundTripDumper, resolver, add_constructor, add_representer

from src.meta.abstract import AbstractMeta
from utils.custom_logging import make_logger
from utils.custom_path import Path

logger = make_logger(__name__)


_yaml_mapping = resolver.BaseResolver.DEFAULT_MAPPING_TAG


def odict_represent(dumper, data):
    return dumper.represent_dict(data.iteritems())


def odict_construct(loader, node):
    return OrderedDict(loader.construct_pairs(node))


add_representer(OrderedDict, odict_represent)
add_constructor(_yaml_mapping, odict_construct)


class Meta(AbstractMeta):

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
        self.free = True
        self.encrypt = encrypted

        if init_dict is None:
            self._data = OrderedDict()

        else:

            if not isinstance(init_dict, OrderedDict):
                raise TypeError('expected a OrderedDict, got "{}"'.format(type(init_dict)))

            self._data = init_dict

        self._values, self._keys, self._items = None, None, None
        self._init_views()

        if isinstance(path, Path):
            pass

        elif isinstance(path, str):
            path = Path(path)

        else:
            raise TypeError('expected a Path or a str, got: {}'.format(type(path)))

        self._path = path

        if auto_read:
            self.read()

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

    # noinspection PyArgumentList
    def _init_views(self):
        self._values = self._data.values()
        self._keys = self._data.keys()
        self._items = self._data.items()

    @property
    def data(self):
        return self._data

    def get_context(self):
        return self.data

    @data.setter
    def data(self, value: OrderedDict):

        if not isinstance(value, OrderedDict):
            raise TypeError('expected a OrderedDict, got "{}"'.format(type(value)))

        self._data = value
        self._init_views()

    def __len__(self):
        # noinspection PyTypeChecker
        return len(self.data)

    def __iter__(self):
        for k in self.keys():
            yield k

    def __contains__(self, x):
        # noinspection PyArgumentList
        return self._data.__contains__(x)

    def __delitem__(self, key, _write=False):
        del self.data[key]

        if _write:
            self.write()

    def __setitem__(self, key, value, _write=False):
        self.data[key] = value

        if _write:
            self.write()

    def __getitem__(self, key):
        return self._data.get(key, None)

    def __str__(self):
        # noinspection PyArgumentList
        return self.data.__str__()

    def __repr__(self):
        return '{}: {}'.format(self.__class__.__name__, self.data.__repr__())

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def items(self):
        return self._items

    def debug(self, txt: str):
        logger.debug('{}: {}'.format(self.path.abspath(), txt))

    def exception(self, txt: str):
        logger.debug('{}: {}'.format(self.path.abspath(), txt))

    def dump(self):
        return ydump(self.data, Dumper=RoundTripDumper, default_flow_style=False)

    def load(self, data):
        self.data = yload(data)

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
    return Meta.read_header(meta_file_path)
