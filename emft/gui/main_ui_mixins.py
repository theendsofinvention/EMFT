# coding=utf-8

from emft.gui.main_ui_progress import MainUiProgress
from emft.gui.main_ui_msgbox import MainUiMsgBox
from emft.gui.main_ui_threading import MainUiThreading


class MainUiMixins(MainUiProgress, MainUiMsgBox, MainUiThreading):
    pass
