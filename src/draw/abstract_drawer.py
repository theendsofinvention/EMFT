# coding=utf-8

import abc
import re
import colour
from .shapes import Poly, Point, Circle


class AbstractDrawer:

    re_color = re.compile('(?P<name>.*)#(?P<color>.*)')

    @abc.abstractmethod
    def save(self, path):
        """"""

    @abc.abstractmethod
    def add_poly(self, poly: Poly, color: colour.Color):
        """"""

    @abc.abstractmethod
    def add_point(self, point: Point, color: colour.Color):
        """"""

    @abc.abstractmethod
    def add_circle(self, circle:Circle, color: colour.Color):
        """"""

    def add_shape(self, shape):

        shape_type = shape['type']
        # if shape_type == 'POINT':
        #     return

        if shape_type == 'POLY':

            m = self.re_color.match(shape['name'])
            if m:
                color = colour.Color(m.group('color'))
                shape['name'] = m.group('name')
            else:
                color = colour.Color(pick_for=shape['name'])

            if shape['name'].startswith('$C'):
                shape['name'] = shape['name'][2:]
                self.add_circle(Circle(shape), color)
            else:
                self.add_poly(Poly(shape), color)

        elif shape_type == 'POINT':
            color = colour.Color('blue')
            self.add_point(Point(shape['lat'], shape['long'], name=shape['name']), color)
        else:
            raise ValueError('Unknown shape type: {}'.format(shape_type))
