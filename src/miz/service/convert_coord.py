# coding=utf-8

from src.miz.mission import Group
import math


class ConvertCoord:
    @staticmethod
    def convert_lat(LO):
        # LO = math.fabs(LO)
        # print(LO)
        poly = [1.7871157276496346e-63, -3.7017105376966803e-56, 3.2739211586271487e-49, -1.61035664804101e-42,
                4.8132831946662597e-36, -8.9716034302632608e-30, 1.0303954202826318e-23, -6.9242087443114205e-18,
                2.5109873548809445e-12, -1.7404291057902361e-07, 34.279300215537305]
        return sum(x * LO**pwr for x, pwr in zip(poly, reversed(range(len(poly)))))
    
    
    @staticmethod
    def convert_long(LO):
        # LO = math.fabs(LO)
        # print(LO)
        poly = [7.7823586472318142e-68, -1.4889802851577457e-60, 9.7709735498211447e-54, -4.0889355382250073e-48,
                -2.1984858913186359e-40, -1.4836779870704244e-34, 1.1548134826958055e-26, 4.6020819684197637e-21,
                -7.0744191595680773e-13, -1.4089631590656565e-07, 45.129497060854682]
        return sum(x * LO**pwr for x, pwr in zip(poly, reversed(range(len(poly)))))
        
    @staticmethod
    def convert_point(point: Group.Route.Point):
        # print(point.x, point.y)
        lat = ConvertCoord.convert_lat(point.x)
        long_ = ConvertCoord.convert_long(point.y)
        return float(lat), float(long_)