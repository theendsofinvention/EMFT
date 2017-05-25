# coding=utf-8

import typing
from collections import OrderedDict

import colour

from .point import Point
from .writable_shape import WritableShape
from src.meta import Meta, MetaPropertyWithDefault, MetaProperty


class Polygon(Meta, WritableShape):

    def __init__(self, **kwargs):
        Meta.__init__(self, init_dict=OrderedDict(kwargs))

    @MetaProperty(list)
    def points(self, value) -> typing.List['Point']:
        return value

    @MetaPropertyWithDefault(colour.Color, colour.Color('black'))
    def color(self, value) -> colour.Color:
        return value

