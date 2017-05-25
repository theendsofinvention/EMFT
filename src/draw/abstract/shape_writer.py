# coding=utf-8


import abc


class ShapeWriter(abc.ABC):

    @abc.abstractmethod
    def write_polygon(self, polygon):
        """"""