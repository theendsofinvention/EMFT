# coding=utf-8
class Shape:

    def __init__(self, name):
        self.name = name


class Point:

    def __init__(self, x, y, alt):
        self.x = float(x)
        self.y = float(y)
        self.alt = float(alt)


class Poly(Shape):

    def __init__(self, poly_string: str):
        self.name, *points = poly_string.split('|')
        Shape.__init__(self, self.name)
        self.__center = None
        # print(list(x.split(',') for x in points))
        self.points = list(Point(*p.split(',')) for p in points)

    @property
    def centre(self):
        if self.__center is None:
            x = [p.x for p in self.points]
            y = [p.y for p in self.points]
            self.__center = (sum(x) / len(self.points), sum(y) / len(self.points))
        return self.__center