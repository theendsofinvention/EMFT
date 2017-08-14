# coding=utf-8
"""
Creates a dispatcher for function calls outside of the main UI.

Calling interface methods from the main application thread will transfer the call to the main UI,
while calling them in a separate thread will take advantage of Qt Signals to transfer them back to Qt
EventLoop.

Any module willing to add methods to the interface should use MainUiMixinsAdapter to do so.
"""

import threading

from emft.core import constant
from emft.gui.main_ui_mixins_adapter import MainUiMixinsAdapter


class MainUiMethod:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if constant.MAIN_UI is None:
            raise RuntimeError('Main UI not initialized')

        # Check if this was called in the main thread (the one running Qt EventLoop)
        # noinspection PyProtectedMember
        if isinstance(threading.current_thread(), threading._MainThread):

            # If we are in the EventLoop, there's no need to dispatch the call to the a signal
            # noinspection PyProtectedMember
            constant.MAIN_UI._do('main_ui', self.func.__name__, args, kwargs)
        else:

            # Otherwise, queue the call
            constant.MAIN_UI.do('main_ui', self.func.__name__, *args, **kwargs)


# noinspection PyAbstractClass
class I(
    MainUiMixinsAdapter,
):
    @MainUiMethod
    def confirm(
            self,
            text: str,
            title: str = None,
            ico: str = None,
            follow_up_on_yes: callable = None,
            follow_up_on_no: callable = None
    ):
        """"""

    @MainUiMethod
    def error(self, text: str, follow_up: callable = None, title: str = None):
        """"""

    @MainUiMethod
    def msg(self, text: str, follow_up: callable = None, title: str = None):
        """"""

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

    @staticmethod
    @MainUiMethod
    def progress_set_value(value: int):
        """"""

    @staticmethod
    @MainUiMethod
    def progress_start(title: str, length: int = 100, label: str = ''):
        """"""

    @staticmethod
    @MainUiMethod
    def progress_set_label(value: str):
        """"""

    @staticmethod
    @MainUiMethod
    def progress_done():
        """"""
