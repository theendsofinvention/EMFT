# coding=utf-8

from src.meta import Meta, MetaProperty


class Radio(Meta):
    def __init__(self, radio_name: str, channels: list = None):
        Meta.__init__(self)
        self.name = radio_name
        self.channels = channels

    @MetaProperty(str)
    def name(self, value):
        return value

    @MetaProperty(list)
    def channels(self, value):
        return value

    def __hash__(self):
        return self.name.__hash__()