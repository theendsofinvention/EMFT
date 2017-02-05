# coding=utf-8

# noinspection PyProtectedMember
from src import _global


class MainUiMethod:

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if _global.MAIN_UI is None:
            raise RuntimeError('Main UI not initialized')
        _global.MAIN_UI.do('main_ui', self.func.__name__, *args, **kwargs)


class I:
    @staticmethod
    @MainUiMethod
    def show_log_tab():
        """"""

    @staticmethod
    @MainUiMethod
    def show():
        """"""

    @staticmethod
    @MainUiMethod
    def hide():
        """"""
