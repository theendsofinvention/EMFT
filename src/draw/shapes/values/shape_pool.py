# coding=utf-8

from collections.abc import MutableSet
import typing
from .writable_shape import WritableShape


class ShapePool(MutableSet):

    def __init__(self, init_data: typing.Set['WritableShape'] = None):

        if init_data is None:
            init_data = set()

        self._data = init_data

    @property
    def data(self) -> typing.Set['WritableShape']:
        return self._data

    def __iter__(self) -> typing.Iterator['WritableShape']:
        return self.data.__iter__()

    def __contains__(self, item: WritableShape) -> bool:
        return self.data.__contains__(item)

    def __len__(self) -> int:
        return self.data.__len__()

    def add(self, value: WritableShape):
        return self.data.add(value)

    def discard(self, value: WritableShape):
        return self.data.discard(value)


