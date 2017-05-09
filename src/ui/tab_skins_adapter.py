# coding=utf-8
import abc

from .itab import MainUiTabMethod

TAB_NAME = 'Skins'


class TabSkinsAdapter:
    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_skins_update_dcs_installs_combo(self):
        """"""

    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_skins_show_skins_scan_result(self, scan_result):
        """"""
