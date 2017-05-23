# coding=utf-8

import typing
from .channel import Channel
from src.meta import Meta, MetaProperty


class Radio(Meta):
    def __init__(
            self,
            radio_name: str,
            min_freq: float,
            max_freq: float,
            channel_qty: int,
            aircrafts: typing.Set[str],
            channels: typing.List['Channel'] = None,
    ):
        Meta.__init__(self)
        self.name = str(radio_name)
        self.channel_qty = int(channel_qty)
        self.min_freq = float(min_freq)
        self.max_freq = float(max_freq)
        self.aircrafts = set(aircrafts)
        self.channels = list(channels) if channels else list()

    @MetaProperty(str)
    def name(self, value) -> str:
        return value

    @MetaProperty(list)
    def channels(self, value) -> typing.List['Channel']:
        return value

    @MetaProperty(int)
    def channel_qty(self, value) -> int:
        return value

    @MetaProperty(float)
    def min_freq(self, value) -> float:
        return value

    @MetaProperty(float)
    def max_freq(self, value) -> float:
        return value

    @MetaProperty(set)
    def aircrafts(self, value) -> typing.Set[str]:
        """List of aircrafts that have this radio"""
        return value

    def __hash__(self):
        return self.name.__hash__()