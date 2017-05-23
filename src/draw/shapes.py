# coding=utf-8
class Shape:

    def __init__(self, name):
        self.name = name


class Point:

    def __init__(self, y, x, alt=0, name=None):
        self.x = float(x)
        self.y = float(y)
        self.alt = float(alt)
        self.name = name


class Circle(Shape):

    def __init__(self, shape_data):
        print(shape_data)
        self.name = shape_data['name']
        Shape.__init__(self, self.name)

        self.center = shape_data


class Poly(Shape):

    def __init__(self, shape_data):
        self.name = shape_data['name']

        Shape.__init__(self, self.name)
        self.__center = None
        # print(list(x.split(',') for x in points))
        self.points = list(Point(*p) for p in shape_data['points'])

    @property
    def centre(self):
        if self.__center is None:
            x = [p.x for p in self.points]
            y = [p.y for p in self.points]
            self.__center = (sum(x) / len(self.points), sum(y) / len(self.points))
        return self.__center