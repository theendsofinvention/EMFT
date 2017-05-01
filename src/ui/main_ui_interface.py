# coding=utf-8


from utils import ProgressAdapter

from src import global_
from .base import WithMsgBoxAdapter


class MainUiMethod:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if global_.MAIN_UI is None:
            raise RuntimeError('Main UI not initialized')
        global_.MAIN_UI.do('main_ui', self.func.__name__, *args, **kwargs)


class I(ProgressAdapter, WithMsgBoxAdapter):
    @MainUiMethod
    def confirm(self, text: str, follow_up: callable, title: str = None, follow_up_on_no: callable = None):
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
    def write_log(value: str, color: str):
        """"""

    @staticmethod
    @MainUiMethod
    def update_config_tab(version_check_result=None):
        """"""

    @staticmethod
    @MainUiMethod
    def tab_reorder_update_view_after_remote_scan():
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
