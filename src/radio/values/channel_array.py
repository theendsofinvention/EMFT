# coding=utf-8

import typing
from collections.abc import Sequence
from .channel import Channel


class ChannelArray(Sequence):
    def __init__(self, init_list: typing.List['Channel'] = None):
        if init_list is None:
            init_list = list()

        self._data = init_list

    def __len__(self) -> int:
        return self.data.__len__()

    def __getitem__(self, index) -> Channel:
        return self.data.__getitem__(index)

    @property
    def data(self) -> typing.List['Channel']:
        return self._data

    def __iter__(self) -> typing.Generator['Channel', None, None]:
        return self.data.__iter__()

    def append(self, item: Channel):
        self.data.append(item)

    def remove(self, item: Channel):
        self.data.remove(item)