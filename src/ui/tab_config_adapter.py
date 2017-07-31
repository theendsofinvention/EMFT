# coding=utf-8

import abc

from src.ui.main_ui_tab_widget import MainUiTabMethod

TAB_NAME = 'Config'


class TabConfigAdapter:
    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def config_tab_update_dcs_installs(self, *args, **kwargs):
        """"""
