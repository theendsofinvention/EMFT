# coding=utf-8

from .main_ui_progress import MainUiProgress
from .main_ui_msgbox import MainUiMsgBox
from .main_ui_threading import MainUiThreading


class MainUiMixins(MainUiProgress, MainUiMsgBox, MainUiThreading):
    pass