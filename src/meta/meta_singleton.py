# coding=utf-8

import abc
from utils.custom_path import Path
from .meta import Meta


class _MetaSingleton(abc.ABCMeta):
    """
    When used as metaclass, allow only one instance of a class
    """

    _instances = {}

    def __call__(cls, file: str or Path, init_d: dict = None):
        if isinstance(file, str):
            file = Path(file)
        elif isinstance(file, Path):
            pass
        else:
            raise TypeError('expected a Path or a str, got: {}'.format(type(file)))

        abs_path = file.abspath()

        if abs_path not in _MetaSingleton._instances:
            _MetaSingleton._instances[abs_path] = super(_MetaSingleton, cls).__call__(file, init_d)
        return _MetaSingleton._instances[abs_path]


class MetaSingleton(Meta, metaclass=_MetaSingleton):
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

    def __init__(self, path: Path or str, init_dict: dict = None, auto_read=True):
        Meta.__init__(self, path, init_dict, auto_read)
