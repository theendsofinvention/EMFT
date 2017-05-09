# coding=utf-8


from utils import ProgressAdapter

from src import global_
from src.ui.main_ui_msgbox_adapter import MainUiMsgBoxAdapter
from .tab_config_adapter import TabConfigAdapter
from .tab_log_adapter import TabLogAdapter
from .tab_reorder_adapter import TabReorderAdapter
from .tab_roster_adapter import TabRosterAdapter
from .main_ui_mixins_adapter import MainUiMixinsAdapter


class MainUiMethod:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if global_.MAIN_UI is None:
            raise RuntimeError('Main UI not initialized')
        global_.MAIN_UI.do('main_ui', self.func.__name__, *args, **kwargs)


class I(MainUiMixinsAdapter, TabConfigAdapter, TabLogAdapter, TabReorderAdapter, TabRosterAdapter):
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
