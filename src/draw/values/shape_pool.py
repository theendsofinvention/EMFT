# coding=utf-8

from collections.abc import MutableSet

from src.draw.values import Polygon, Point, NamedPoint


class ShapePool(MutableSet):

    def __init__(self, init_data: set = None):

        if init_data is None:
            init_data = set()

        self._data = init_data

    @property
    def data(self) -> set:
        return self._data

    def __iter__(self):
        return self.data.__iter__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __len__(self):
        return self.data.__len__()

    def add(self, value):
        return self.data.add(value)

    def discard(self, value):
        return self.data.discard(value)


