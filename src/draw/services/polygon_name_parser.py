# coding=utf-8

import typing

import colour

from src.draw.values import Param

valid_params = dict(
    color=('color', 'c', 'colour', 'col'),
    radius=('radius', 'rad', 'r'),
    group=('group', 'g', 'grp')
)

valid_params_lookup = {x: k for k in valid_params for x in valid_params[k]}


class PolygonNameParser:
    def __init__(self):
        pass

    def parse_tag_color(self, value_str):
        try:
            return colour.Color(value_str)
        except ValueError:
            raise ValueError(
                (
                    '"{}" is not a recognized color.\n'
                    'Valid colors are 3 or 6 digits hex codes, or one of:\n'
                    '{}'
                ).format(value_str, ', '.join(sorted(k for k in colour.COLOR_NAME_TO_RGB)))
            )

    def parse_tag_radius(self, value_str):
        return value_str

    def parse_tag_group(self, value_str):
        return value_str

    def polygon_name_to_params(self, poly_name) -> typing.Tuple[str, typing.Set[Param]]:
        name, *params_str = poly_name.split('@')
        params = [Param('name', name)]
        for x in params_str:
            params.append(self.parse_param_str(x))
        return name, params

    def parse_param_str(self, param_str):

        try:
            qualifier, value = param_str.split('_')
        except ValueError:
            raise ValueError(
                (
                    'Wrong format for parameter: {}\n'
                    'Use an underscore ("_") to separate your tag and your value.'
                ).format(param_str)
            )

        qualifier = qualifier.lower()

        try:
            qualifier = valid_params_lookup[qualifier]
        except KeyError:
            raise ValueError(
                (
                    'Invalid tag: {}\n'
                    'Valid tags are: {!r}'
                ).format(
                    qualifier,
                    list(value[0] for value in valid_params.values()),
                )
            )

        tag = 'parse_tag_{}'.format(qualifier)

        if not hasattr(self, tag):
            raise AttributeError('unknown parameter: {}'.format(qualifier))

        value = getattr(self, tag)(value)

        return qualifier, value
