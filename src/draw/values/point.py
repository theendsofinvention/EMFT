# coding=utf-8

from src.meta import Meta, MetaProperty


class Point(Meta):
    def __init__(self, lat: float, long: float, alt: float = 0):
        Meta.__init__(self)
        self.lat = lat
        self.long = long
        self.alt = alt

    @staticmethod
    def __convert_int(value):
        # I'm ok with this
        if isinstance(value, int):
            return float(value)
        return value

    @MetaProperty(float)
    def lat(self, value):
        value = self.__convert_int(value)
        return value

    @MetaProperty(float)
    def long(self, value):
        value = self.__convert_int(value)
        return value

    @MetaProperty(float)
    def alt(self, value):
        value = self.__convert_int(value)
        if value < 0:
            raise ValueError('negative altitude not allowed')
        return value