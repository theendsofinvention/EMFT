# coding=utf-8

# noinspection PyProtectedMember
from src import _global
from src.utils.singleton import Singleton


class Progress(Singleton):
    @staticmethod
    def start(title: str, length: int, label: str = ''):
        if _global.MAIN_UI:
            _global.MAIN_UI.do('main_ui', 'progress_start', title, label, length)

    @staticmethod
    def set_value(value):
        if _global.MAIN_UI:
            _global.MAIN_UI.do('main_ui', 'progress_set_value', value)

    @staticmethod
    def set_label(value):
        if _global.MAIN_UI:
            _global.MAIN_UI.do('main_ui', 'progress_set_label', value)

    @staticmethod
    def done():
        if _global.MAIN_UI:
            _global.MAIN_UI.do('main_ui', 'progress_done')
