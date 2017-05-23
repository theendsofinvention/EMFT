# coding=utf-8

from src.meta import Meta, MetaProperty


class Channel(Meta):
    def __init__(self, channel_number: int, frequency: float, description: str):
        Meta.__init__(self)
        self.channel_number = channel_number
        self.frequency = frequency
        self.description = description

    @MetaProperty(int)
    def channel_number(self, value):
        return value

    @MetaProperty(float)
    def frequency(self, value):
        return value

    @MetaProperty(str)
    def description(self, value):
        return value
