# coding=utf-8

from .point import Point
from .writable_shape import WritableShape


class NamedPoint(Point, WritableShape):

    def __init__(self, **kwargs):
        Point.__init__(self, **kwargs)
