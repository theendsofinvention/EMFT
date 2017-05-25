# coding=utf-8

from src.meta import MetaProperty, MetaPropertyWithDefault


class WritableShape:
    @MetaProperty(str)
    def name(self, value: str) -> str:
        return value

    @MetaPropertyWithDefault('none', str)
    def group(self, value: str) -> str:
        return value