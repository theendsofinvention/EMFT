# coding=utf-8
import typing
from collections import MutableSequence

from src.utils import make_logger, Singleton

logger = make_logger(__name__)


# noinspection PyAbstractClass
class Branch:
    __slots__ = ['name']

    def __init__(
            self,
            name: str,
    ):
        self.name = name


class Branches(MutableSequence, metaclass=Singleton):
    ACTIVE_BRANCH = None

    def __init__(self, init_list: list = None):
        self._data = init_list or list()

    def __getitem__(self, index) -> Branch:
        return self._data.__getitem__(index)

    def __delitem__(self, index):
        return self._data.__delitem__(index)

    def insert(self, index, value: Branch):
        return self._data.insert(index, value)

    def __setitem__(self, index, value):
        return self._data.__setitem__(index, value)

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> typing.Iterator[Branch]:
        return self._data.__iter__()
