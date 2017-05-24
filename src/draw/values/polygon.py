# coding=utf-8

import typing

from src.meta import Meta, MetaProperty
from collections import OrderedDict
from src.draw.values import Point


class Polygon(Meta):

    def __init__(self, **kwargs):
        Meta.__init__(self, init_dict=OrderedDict(kwargs))

    @MetaProperty(str)
    def name(self, value: str) -> str:
        return value

    @MetaProperty(list)
    def points(self, value) -> typing.List['Point']:
        return value