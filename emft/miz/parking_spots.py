# coding=utf-8

import math
import pickle
from collections import namedtuple

from ._parking_spots import parkings
from .mission import Static

ParkingSpot = namedtuple('ParkingSpot', 'airport spot')
parkings = pickle.loads(parkings)


def clear_farps():
    parkings['FARP'] = {}


def add_farp(farp: Static):
    parkings['FARP'][farp.static_name] = farp.static_position


def unit_pos_to_spot(unit_pos) -> ParkingSpot:
    min_ = 50
    res = None
    for airport in parkings:
        for spot in parkings[airport]:
            spot_pos = parkings[airport][spot]
            dist = math.hypot(unit_pos[0] - spot_pos[0], unit_pos[1] - spot_pos[1])
            if dist < min_:
                min_ = dist
                res = ParkingSpot(airport=airport, spot=spot)
    return res
