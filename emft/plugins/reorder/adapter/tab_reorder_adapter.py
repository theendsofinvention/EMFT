# coding=utf-8

import abc

from emft.gui.main_ui_tab_widget import MainUiTabMethod

TAB_NAME = 'Reorder MIZ'


class TabReorderAdapter:
    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_reorder_update_view_after_artifact_scan(self, *args, **kwargs):
        """"""

    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_reorder_update_view_after_branches_scan(self, *args, **kwargs):
        """"""

    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_reorder_change_active_profile(self, *args, **kwargs):
        """"""
