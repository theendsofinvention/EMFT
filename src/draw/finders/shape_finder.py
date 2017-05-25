# coding=utf-8
import typing
from operator import attrgetter
from src.draw.values import Polygon, Point, NamedPoint, ShapePool
from src.draw.abstract import WritableShape


class ShapeFinder:

    @staticmethod
    def get_polygons(pool: ShapePool) -> ShapePool:
        new_pool = ShapePool()
        for shape in pool:
            if isinstance(shape, Polygon):
                new_pool.add(shape)
        return sorted(new_pool, key=attrgetter('group', 'name'))

    @staticmethod
    def find_by_name(pool: ShapePool, shape_name: str) -> WritableShape:
        for shape in pool:
            if shape.name == shape_name:
                return shape
        raise IndexError('shape not found: "{}"'.format(shape_name))