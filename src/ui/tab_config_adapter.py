# coding=utf-8

import abc

from src.ui.itab import MainUiTabMethod

TAB_NAME = 'Config'


class TabConfigAdapter:
    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def config_tab_update_dcs_installs(self, *args, **kwargs):
        """"""

    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def config_tab_update_latest_release(self, *args, **kwargs):
        """"""
