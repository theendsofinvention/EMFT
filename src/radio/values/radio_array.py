# coding=utf-8

import typing
from collections import OrderedDict
from collections.abc import Sequence
from .radio import Radio


class RadioArray(Sequence):
    def __init__(self, init_list: typing.List['Radio'] = None):
        if init_list is None:
            init_list = list()

        self._data = init_list

    def __len__(self) -> int:
        return self.data.__len__()

    def __getitem__(self, index) -> Radio:
        return self.data.__getitem__(index)

    @property
    def data(self) -> typing.List['Radio']:
        return self._data

    def __iter__(self) -> typing.Generator['Radio', None, None]:
        return self.data.__iter__()

    def append(self, item: Radio):
        self.data.append(item)

    def remove(self, item: Radio):
        self.data.remove(item)