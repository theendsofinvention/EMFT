# coding=utf-8

import abc

from emft.utils import ThreadPool


class MainUiThreadingAdapter:
    @property
    @abc.abstractmethod
    def pool(self) -> ThreadPool:
        """"""
