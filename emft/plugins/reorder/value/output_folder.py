# coding=utf-8
import typing
from collections import MutableMapping

from emft.core.logging import make_logger
from emft.core.path import Path
from emft.core.singleton import Singleton

LOGGER = make_logger(__name__)


# noinspection PyAbstractClass
class OutputFolder(Path):
    pass


class OutputFolders(MutableMapping, metaclass=Singleton):
    ACTIVE_OUTPUT_FOLDER = None
    ACTIVE_OUTPUT_FOLDER_NAME = None

    def __init__(self, init_dict: dict = None):
        self._data = init_dict or dict()

    def __getitem__(self, key) -> OutputFolder:
        return self._data.__getitem__(key)

    def __iter__(self) -> typing.Iterator[str]:
        return self._data.__iter__()

    def values(self) -> typing.List[OutputFolder]:
        return list(self._data.values())

    @property
    def data(self) -> dict:
        return self._data

    def __len__(self) -> int:
        return self._data.__len__()

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __setitem__(self, key, value: OutputFolder):
        return self._data.__setitem__(key, value)
