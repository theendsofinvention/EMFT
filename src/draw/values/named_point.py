# coding=utf-8

from src.draw.values import Point
from src.draw.abstract import WritableShape


class NamedPoint(Point, WritableShape):

    def __init__(self, **kwargs):
        Point.__init__(self, **kwargs)
