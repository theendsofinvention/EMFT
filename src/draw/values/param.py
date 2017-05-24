# coding=utf-8

from src.meta import MetaProperty, Meta


class Param(Meta):
    def __init__(self, name: str, value: object):
        Meta.__init__(self)
        self.name = name
        self.value = value

    @MetaProperty(str)
    def name(self, value):
        return value

    @MetaProperty(object)
    def value(self, value):
        return value
