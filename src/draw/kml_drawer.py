# coding=utf-8
import colour
import simplekml

from .abstract_drawer import AbstractDrawer
from .old_shapes import Poly, Point, Circle


class KMLDrawer(simplekml.Kml, AbstractDrawer):
    def __init__(self, name: str):
        simplekml.Kml.__init__(self)

        self.document.name = name

        self.polygon_folder = self.newfolder()
        assert isinstance(self.polygon_folder, simplekml.Folder)
        self.polygon_folder.name = 'Polygons'

        self.points_folder = self.newfolder()
        assert isinstance(self.points_folder, simplekml.Folder)
        self.points_folder.name = 'Points'

    def add_circle(self, circle:Circle, color: colour.Color):
        pass

    def add_point(self, shape: Point, color: colour.Color):

        point = self.points_folder.newpoint()
        point.name = shape.name or ''
        point.coords = [[shape.x, shape.y,]]
        point.style.iconstyle.scale = 0.5
        point.style.labelstyle.color = simplekml.Color.rgb(*(int(x * 255) for x in color.rgb), 255)
        point.style.iconstyle.icon.href = r'http://maps.google.com/mapfiles/kml/shapes/donut.png'
        # point = self.newpoint()

    def add_poly(self, poly_: 'Poly', color: colour.Color):


        folder = self.polygon_folder.newfolder()
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
            color=simplekml.Color.rgb(*(int(x * 255) for x in color.rgb), 50),
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
        center.style.labelstyle.color = simplekml.Color.rgb(*(int(x * 255) for x in color.rgb), 255)
        # print(poly_.centre)
        center.coords = [poly_.centre]
