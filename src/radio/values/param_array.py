# coding=utf-8

from src.meta import Meta, MetaProperty


class ParamArray(Meta):
    def __init__(self, params: list):
        Meta.__init__(self)
        self._values = params

    @MetaProperty(list)
    def params(self, value):
        return value
