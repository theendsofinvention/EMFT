# coding=utf-8

import abc
from .shapes import Poly, Point


class AbstractDrawer:

    @abc.abstractmethod
    def save(self, path):
        """"""

    @abc.abstractmethod
    def add_poly(self, poly: Poly, color):
        """"""

    @abc.abstractmethod
    def add_point(self, point: Point, color):
        """"""
