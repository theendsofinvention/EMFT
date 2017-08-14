# coding=utf-8
import abc

from emft.core import constant
from emft.gui.base import TabChild


class MainUiTabChild(TabChild):

    def __init__(self, parent):
        TabChild.__init__(self, parent)
        self._main_ui = parent

    @abc.abstractmethod
    def tab_clicked(self):
        raise NotImplementedError()


class _MainUiTabMethod:
    def __init__(self, func, tab_name):
        self.func = func
        self.tab_name = tab_name

    def __call__(self, *args, **kwargs):
        if constant.MAIN_UI is None:
            raise RuntimeError('Main UI not initialized')
        constant.MAIN_UI.do('tab_{}'.format(self.tab_name), self.func.__name__, *args, **kwargs)


class MainUiTabMethod:
    """
    Decorator-class to create properties for META instances.
    """

    def __init__(self, tab_name: str):
        self.tab_name = tab_name

    def __call__(self, func: callable):
        """
        Creates a DESCRIPTOR instance for a method of a META instance.

        :param func: function to decorate
        :return: decorated function as a descriptor instance of _MetaProperty
        :rtype: _MetaProperty
        """
        return _MainUiTabMethod(func, self.tab_name)
