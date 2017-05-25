# coding=utf-8

from collections import OrderedDict
from src.meta import Meta, MetaProperty


class Point(Meta):
    def __init__(self, **kwargs):
        Meta.__init__(self, init_dict=OrderedDict(kwargs))

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