# coding=utf-8

import typing
from collections.abc import MutableMapping
from .output_folder import OutputFolder
from src.utils import Singleton


class OutputFolders(MutableMapping, metaclass=Singleton):
    def __init__(self, init_dict: dict = None):
        self._data = init_dict or dict()

    def __getitem__(self, key) -> OutputFolder:
        return self._data.__getitem__(key)

    def __iter__(self) -> typing.Iterator[str]:
        return self._data.__iter__()

    def values(self) -> typing.Iterator[OutputFolder]:
        return self._data.values()

    @property
    def data(self) -> dict:
        return self._data

    def __len__(self) -> int:
        return self._data.__len__()

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __setitem__(self, key, value: OutputFolder):
        return self._data.__setitem__(key, value)