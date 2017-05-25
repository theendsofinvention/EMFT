# coding=utf-8

import simplekml

from src.draw import abstract
from src.draw.shapes.values import Polygon


class KMLWriter(simplekml.Kml, abstract.ShapeWriter):

    def __init__(self, document_name: str):
        simplekml.Kml.__init__(self)

        self.document.name = document_name

    def write_polygon(self, polygon: Polygon):
        pass
