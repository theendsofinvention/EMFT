# coding=utf-8
import datetime
import uuid
from json import dumps
from .shapes import Poly, Point
from .abstract_drawer import AbstractDrawer


class JSONDrawer(AbstractDrawer):

    def __init__(self, name: str):
        self.data = {
            'drawings': []
        }
        self.name = name
        self.time = '{0.day:02}.{0.month:02}.{0.year}-{0.hour:02}:{0.minute:02}:{0.second:02}'.format(
            datetime.datetime.utcnow())


    def __add_shape(self, shape):
        self.data['drawings'].append(shape)

    def add_poly(self, poly: 'Poly', color):

        def add_point(point):
            d['points'].append(
                dict(
                    x=point.x,
                    y=point.y
                )
            )

        d = {
            'author': 'EMFT',
            'timestamp': self.time,
            'type': 'polygon',
            'name': poly.name,
            'id': '{{{}}}'.format(uuid.uuid4().__str__()),
            'color': '#ff{}'.format(color),
            'colorBg': '#33{}'.format(color),
            'brushStyle': 5,
            'lineWidth': 1,
            'points': [
                dict(x=p.x, y=p.y) for p in poly.points
            ],
            'shared': True,
        }
        # for point in poly.points:
        #     add_point(point)

        self.__add_shape(d)

        d = {
            'author': 'EMFT',
            'timestamp': self.time,
            'type': 'text',
            'name': '',
            'id': '{{{}}}'.format(uuid.uuid4().__str__()),
            'color': '#ff{}'.format(color),
            'colorBg': '#ff{}'.format(color),
            'brushStyle': 1,
            'lineWidth': 1,
            'font': 'Calibri,8,-1,5,50,0,0,0,0,0',
            'pos_x': poly.centre[0],
            'pos_y': poly.centre[1],
            'shared': True,
            'text': poly.name
        }

        self.__add_shape(d)


    def save(self, path: str):
        with open(path, mode='w') as f:
            f.write(dumps(self.data, indent=True, sort_keys=True))