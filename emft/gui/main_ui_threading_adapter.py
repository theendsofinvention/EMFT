# coding=utf-8

import abc

from emft.core.threadpool import ThreadPool


class MainUiThreadingAdapter:
    @property
    @abc.abstractmethod
    def pool(self) -> ThreadPool:
        """"""
