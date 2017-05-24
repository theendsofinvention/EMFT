# coding=utf-8

from .point import Point, MetaProperty


class NamedPoint(Point):

    def __init__(self, name: str, lat: float, long: float, alt: float = 0):
        Point.__init__(self, lat, long, alt)
        self.name = name

    @MetaProperty(str)
    def name(self, value):
        return value
