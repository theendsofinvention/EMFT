# coding=utf-8
from utils import ProgressAdapter

from src import global_


class MainUIProgressAdapter(ProgressAdapter):
    @staticmethod
    def __progress_wrapper(func_name, *args, **kwargs):
        if global_.MAIN_UI:
            global_.MAIN_UI.do('main_ui', func_name, *args, **kwargs)

    @staticmethod
    def progress_set_value(value: int):
        MainUIProgressAdapter.__progress_wrapper('progress_set_value', value)

    @staticmethod
    def progress_start(title: str, length: int = 100, label: str = ''):
        MainUIProgressAdapter.__progress_wrapper('progress_start', title, length, label)

    @staticmethod
    def progress_set_label(value: str):
        MainUIProgressAdapter.__progress_wrapper('progress_set_label', value)

    @staticmethod
    def progress_done():
        MainUIProgressAdapter.__progress_wrapper('progress_done')