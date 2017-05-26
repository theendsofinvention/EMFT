# coding=utf-8
import typing
from operator import attrgetter

from ..values import Polygon, ShapePool, WritableShape


class ShapeFinder:

    @staticmethod
    def __sorted_polygons_pool(pool: ShapePool) -> typing.MutableSet['Polygon']:
        return sorted(pool, key=attrgetter('group', 'name'))

    @classmethod
    def get_polygons_belonging_to_group(cls, pool: ShapePool, group_name: str) -> typing.MutableSet['Polygon']:
        polygons = ShapePool(set(shape for shape in ShapeFinder.get_polygons(pool) if shape.group == group_name))
        return cls.__sorted_polygons_pool(polygons)


    @classmethod
    def get_polygons(cls, pool: ShapePool) -> typing.MutableSet['Polygon']:
        return cls.__sorted_polygons_pool(ShapePool(set(shape for shape in pool if isinstance(shape, Polygon))))

    @staticmethod
    def get_available_groups(pool: ShapePool) -> typing.List[str]:
        return sorted(set(polygon.group for polygon in ShapeFinder.get_polygons(pool) if polygon.group))

    @staticmethod
    def find_by_name(pool: ShapePool, shape_name: str) -> WritableShape:
        for shape in pool:
            if shape.name == shape_name:
                return shape
        raise IndexError('shape not found: "{}"'.format(shape_name))