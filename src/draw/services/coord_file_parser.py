# coding=utf-8

import typing
import json
import re
from utils import Path
from src.draw.values import NamedPoint, Polygon, Point
from .polygon_name_parser import PolygonNameParser


class CoordFileParser:

    def __init__(self, skip_points_regex_str_list: typing.List[str] = None):
        if skip_points_regex_str_list is None:
            skip_points_regex_str_list = list()
        self.skip_points = [re.compile(pattern) for pattern in skip_points_regex_str_list]
        self.polygon_name_parser = PolygonNameParser()

    def parse_shape_POLY(self, shape_dictionary: dict):
        shape_dictionary['points'] = [
            Point(**kwargs) for kwargs in shape_dictionary['points']
        ]

        shape_dictionary.update(self.polygon_name_parser.polygon_name_to_params(shape_dictionary['name']))



        return Polygon(**shape_dictionary)

    def parse_shape_POINT(self, shape_dictionary):
        point_name = shape_dictionary['name']
        for regex_object in self.skip_points:
            if regex_object.match(point_name):
                return None
        return NamedPoint(**shape_dictionary)

    def parse_line(self, line):
        d = json.loads(line.strip())

        shape_parser = 'parse_shape_{}'.format(d['type'])

        if not hasattr(self, shape_parser):
            raise AttributeError('unknown shape: {}'.format(shape_parser))

        del d['type']

        return getattr(self, shape_parser)(d)

    def parse_file_into_shapes(self, file_path: str or Path):

        shapes = set()
        for line in Path(file_path).lines():
            shapes.add(self.parse_line(line))

        shapes.remove(None)

        return sorted(shapes, key=lambda x: x.name)
