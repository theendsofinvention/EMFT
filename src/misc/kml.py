# coding=utf-8

import simplekml
import random
import uuid

import datetime
from json import dumps


def _random_color():
    r = lambda: random.randint(0, 255)
    return '50%02X%02X%02X' % (r(), r(), r())


def get_spaced_colors(n):
    max_value = 16581375  # 255**3
    interval = int(max_value / n)
    colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]

    return colors
    return ['50{}'.format(color) for color in colors]
    return [(i[:2], i[2:4], i[4:]) for i in colors]
    return [(int(i[:2], 16), int(i[2:4], 16), int(i[4:], 16)) for i in colors]


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



class JSON:

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



class KML(simplekml.Kml):

    def __init__(self, name: str):
        simplekml.Kml.__init__(self)

        self.document.name = name

    def add_poly(self, poly_:'Poly', color):
        # print(points)
        # for p in points:
        #     print(tuple(p.split(',')))
        # return

        folder = self.newfolder()
        assert isinstance(folder, simplekml.Folder)
        folder.name = poly_.name


        # poly = self.newpolygon(name=poly_.name)
        poly = folder.newpolygon(name=poly_.name)

        assert isinstance(poly, simplekml.Polygon)
        poly.altitudemode = simplekml.AltitudeMode.relativetoground
        poly.extrude = 1
        poly.polystyle = simplekml.PolyStyle(
            fill=1,
            outline=1,
            color='50{}'.format(color),
            colormode=simplekml.ColorMode.normal
        )

        poly.outerboundaryis = list(
            # tuple(p.split(', ')) for p in poly.points
            (p.x, p.y, p.alt) for p in poly_.points
        )

        center = folder.newpoint()
        assert isinstance(center, simplekml.Point)
        center.name = poly_.name
        center.style.iconstyle.scale = 0.8
        print(poly_.centre)
        center.coords = [poly_.centre]


if __name__ == '__main__':
    # print(get_spaced_colors(20)[1:])
    # exit(0)
    l = r'MOA_A-A_SOUTH|42.24150611832, 42.010711944801, 2000|42.087541069392, 40.920969682081, 2519|43.791445751723, 40.777584772319, 2519|43.97569721989, 41.86374199029, 2519|42.241536695988, 42.01068388203, 2519'
    l = '''TIANETI_RANGE|45.334010253098, 41.864413173918, 2000|45.177200245711, 41.781945809259, 2000|44.755023143246, 41.999172667628, 2000|44.84242545295, 42.072674939054, 2000|44.837698844095, 42.222991602396, 2000|44.883529894699, 42.317817121144, 2000|45.328345948285, 42.318336671956, 2000|45.177200245711, 41.781945809259, 2000
MOA_A-A_SOUTH|42.24150611832, 42.010711944801, 2000|42.087541069392, 40.920969682081, 2519|43.791445751723, 40.777584772319, 2519|43.97569721989, 41.86374199029, 2519|42.241536695988, 42.01068388203, 2519
MOA_NORTH|43.975708861364, 41.863748449142, 2000|43.979433565813, 42.221011297504, 2000|43.348996968161, 42.321684703684, 2000|43.082374256286, 42.098181175234, 2000|42.8354942002, 42.151572706993, 2000|42.778942787537, 41.96793200928, 2000|43.975707569565, 41.863740988883, 2000
TETRA|44.143720105125, 41.719257763502, 2000|44.245774464599, 41.455481728236, 2000|44.198169180408, 41.688890085994, 2000|44.709502722663, 41.655848911615, 2000|44.713993403202, 41.445854397192, 2000|44.504603720499, 41.334293182313, 2000|44.245763333163, 41.455516252279, 2000
MARNUELI_RANGE|45.061929127875, 41.300503937719, 2000|45.072442426814, 41.32999927885, 2000|44.89091794792, 41.222189910623, 2000|44.676325944545, 41.299223553312, 2000|44.841006918962, 41.467070132481, 2000|45.072435853811, 41.329999978718, 2000
DUSHETI_RANGE|44.318344595122, 42.105893750229, 2000|44.412275051214, 41.995924662274, 2000|44.482186996642, 42.176983642685, 2000|44.678170499349, 42.250004771351, 2000|44.837708750804, 42.222988036908, 2000|44.842429150036, 42.072674552001, 2000|44.755030255411, 41.999174456867, 2000|44.617658400539, 41.960620101077, 2000|44.412281708262, 41.995923991532, 2000
TKIBULI_RANGE|42.753688511376, 42.298744493742, 2000|42.898653944573, 42.542535525397, 2000|43.28031938944, 42.563819448169, 2000|43.348996968161, 42.321684703684, 2000|43.082373857091, 42.09817868135, 2000|42.8354942002, 42.151572706993, 2000|42.75430191141, 42.299303438258, 2000
KUTAISI MOA|42.428899927627, 42.390718999854, 2000|42.241536695988, 42.01068388203, 2000|42.778942787537, 41.96793200928, 2000|42.8354942002, 42.151572706993, 2000|42.754308636663, 42.299302860604, 2000|42.428898397029, 42.390708866388, 2000'''
    t = KML('test')
    j = JSON('test')

    polys = l.split('\n')
    colors = get_spaced_colors(len(polys)+6)
    for poly_str, color in zip(polys, colors[3:-3]):
        poly = Poly(poly_str)
        t.add_poly(poly, color)
        j.add_poly(poly, color)
    t.save('./test.kml')
    j.save('./test.json')