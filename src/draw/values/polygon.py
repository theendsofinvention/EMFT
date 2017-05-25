# coding=utf-8

import typing
import colour

from src.meta import Meta, MetaPropertyWithDefault, MetaProperty
from collections import OrderedDict
from src.draw.values import Point
from src.draw.abstract import WritableShape


class Polygon(Meta, WritableShape):

    def __init__(self, **kwargs):
        Meta.__init__(self, init_dict=OrderedDict(kwargs))

    @MetaProperty(list)
    def points(self, value) -> typing.List['Point']:
        return value

    @MetaPropertyWithDefault(colour.Color, colour.Color('black'))
    def color(self, value) -> colour.Color:
        return value

