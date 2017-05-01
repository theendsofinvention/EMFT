# coding=utf-8

from .main_ui_msgbox_adapter import MainUiMsgBoxAdapter
from .main_ui_progress_adapter import MainUIProgressAdapter
from .main_ui_threading_adapter import MainUiThreadingAdapter


# noinspection PyAbstractClass
class MainUiMixinsAdapter(MainUIProgressAdapter, MainUiMsgBoxAdapter, MainUiThreadingAdapter):
    pass
