# coding=utf-8

import abc

from src.utils import ThreadPool


class MainUiThreadingAdapter:
    @property
    @abc.abstractmethod
    def pool(self) -> ThreadPool:
        """"""
