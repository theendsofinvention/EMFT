# coding=utf-8

import abc

from src.ui.itab import MainUiTabMethod

TAB_NAME = 'Reorder lua tables'


class TabReorderAdapter:
    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_reorder_update_view_after_remote_scan(self, *args, **kwargs):
        """"""
