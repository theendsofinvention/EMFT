# coding=utf-8
import simplekml


class KMLDrawer(simplekml.Kml):

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