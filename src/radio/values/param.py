# coding=utf-8

from src.meta import Meta, MetaProperty
import colour


class Param(Meta):
    def __init__(self, name: str, value: object):
        Meta.__init__(self)
        self.name = name
        self.value = value

    @MetaProperty(str)
    def name(self, value):
        return value

    @MetaProperty(object)
    def value(self, value):
        return value


class Params(Meta):
    def __init__(self, params: list):
        Meta.__init__(self)
        self._values = params

    @MetaProperty(list)
    def params(self, value):
        return value


class Shape(Meta):
    def __init__(self, name, params=None):
        Meta.__init__(self)
        self.name = name
        self.params = params or list()

    @MetaProperty(str)
    def name(self, value):
        return value

    @MetaProperty(list)
    def params(self, value):
        return value


class Point(Meta):  # TODO move to shapes
    def __init__(self, lat: float, long: float, alt: float = 0):
        Meta.__init__(self)
        self.lat = lat
        self.long = long
        self.alt = alt

    @staticmethod
    def __convert_int(value):
        # I'm ok with this
        if isinstance(value, int):
            return float(value)
        return value

    @MetaProperty(float)
    def lat(self, value):
        value = self.__convert_int(value)
        return value

    @MetaProperty(float)
    def long(self, value):
        value = self.__convert_int(value)
        return value

    @MetaProperty(float)
    def alt(self, value):
        value = self.__convert_int(value)
        if value < 0:
            raise ValueError('negative altitude not allowed')
        return value


class NamedPoint(Shape, Point):
    def __init__(self, name: str, params: Params, lat: float, long: float, alt: float = 0):
        super(NamedPoint, self).__init__(name=name, params=params, lat=lat, long=long, alt=alt)
        # Shape.__init__(self, name, params)
        # Point.__init__(self, lat, long, alt)


class Poly(Shape):
    def __init__(self, name, params, points):
        Shape.__init__(self, name)


valid_params = dict(
    color=('color', 'c', 'colour', 'col'),
    radius=('radius', 'rad', 'r'),
    group=('group', 'g', 'grp')
)

valid_params_lookup = {x: k for k in valid_params for x in valid_params[k]}


def parse_color(color_str):
    try:
        return colour.Color(color_str)
    except ValueError:
        raise ValueError(
            (
                '"{}" is not a recognized color.\n'
                'Valid colors are 3 or 6 digits hex codes, or one of:\n'
                '{}'
            ).format(color_str, ', '.join(sorted(k for k in colour.COLOR_NAME_TO_RGB)))
        )


params_handlers = dict(
    color=parse_color,
    group=print,
    radius=print,
)

handlers_ = set(k for k in params_handlers)
params_ = set(k for k in valid_params)

missing_params = handlers_ - params_
if missing_params:
    raise NotImplementedError('missing parameter in "valid_params" dict: {}'.format(missing_params))

missing_handlers = params_ - handlers_
if missing_handlers:
    raise NotImplementedError('missing handler in "params_handler" dict: {}'.format(missing_handlers))


def parse_param_str(param_str: str):
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

    value = params_handlers[qualifier](value)

    return qualifier, value


def parse_waypoint_string(input_: str):
    name, *params_str = input_.split('@')

    params = []
    param_name = Param('name', name)
    params.append(param_name)

    for param_str in params_str:
        param = Param(*parse_param_str(param_str))
        params.append(param)

    params = Params(list(params))
    return params

if __name__ == '__main__':


    example_waypoint_str = [
        'name@C_red',
        'n@COLOUR_green',
        'n@color_blue',
    ]

    for waypoint_str in example_waypoint_str:
        waypoint_params = parse_waypoint_string(waypoint_str)
        print(waypoint_params)

    example_points = [
        [32.234, 22.234, 500]
    ]

    for point in example_points:
        p = Point(*point)
        print(p)

    example_named_points = [
        ['point1', waypoint_params, 32.234, 22.234, 500]
    ]

    for named_point_str in example_named_points:
        named_point = NamedPoint(*named_point_str)
        print(named_point)
