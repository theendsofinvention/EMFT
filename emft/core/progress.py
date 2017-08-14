# coding=utf-8

import typing
from abc import abstractmethod


class ProgressAdapter:
    @staticmethod
    @abstractmethod
    def progress_start(title: str, length: int = 100, label: str = ''):
        """"""

    @staticmethod
    @abstractmethod
    def progress_set_value(value: int):
        """"""

    @staticmethod
    @abstractmethod
    def progress_set_label(value: str):
        """"""

    @staticmethod
    @abstractmethod
    def progress_done():
        """"""


class Progress:
    def __init__(self):
        raise RuntimeError('do NOT instantiate')

    adapters = []
    title = None
    label = None
    value = 0
    length = 100
    started = False

    @staticmethod
    def _check_adapter(adapter: typing.Type[ProgressAdapter]):
        if not issubclass(adapter, ProgressAdapter):
            raise TypeError(adapter.__class__)

    @staticmethod
    def has_adapter(adapter: typing.Type[ProgressAdapter]):
        return adapter in Progress.adapters

    @staticmethod
    def register_adapter(adapter: typing.Type[ProgressAdapter]):
        Progress._check_adapter(adapter)
        if Progress.has_adapter(adapter):
            return
        Progress.adapters.append(adapter)

    @staticmethod
    def unregister_adapter(adapter: typing.Type[ProgressAdapter]):
        if Progress.has_adapter(adapter):
            Progress.adapters.remove(adapter)

    @staticmethod
    def start(title: str, length: int = 100, label: str = '', start_value: int = 0):
        if Progress.started:
            raise RuntimeError(f'progress already started with {Progress.title}')
        if length < 1:
            raise ValueError(length)
        Progress.started = True
        Progress.set_value(start_value)
        Progress.set_label(label)
        Progress.set_title(title)
        Progress.set_length(length)
        for adapter in Progress.adapters:
            adapter.progress_start(title, length, label)

    @staticmethod
    def set_value(value: (int, float)):
        if not isinstance(value, (int, float)):
            raise TypeError(type(value))
        if value > Progress.length:
            raise ValueError(value)
        for adapter in Progress.adapters:
            adapter.progress_set_value(value)
        Progress.value = value
        if value == Progress.length:
            Progress.done()

    @staticmethod
    def set_label(value: str):
        if not isinstance(value, str):
            raise TypeError(type(value))
        Progress.label = value
        for adapter in Progress.adapters:
            adapter.progress_set_label(value)

    @staticmethod
    def set_length(value: int):
        if not isinstance(value, int):
            raise TypeError(value)
        if value < 1:
            raise ValueError(value)
        Progress.length = value

    @staticmethod
    def set_title(value: str):
        if not isinstance(value, str):
            raise TypeError(type(value))
        Progress.title = value

    @staticmethod
    def done():
        Progress.started = False
        for adapter in Progress.adapters:
            adapter.progress_done()
