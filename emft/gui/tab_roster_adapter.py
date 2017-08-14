# coding=utf-8
import abc
from emft.gui.main_ui_tab_widget import MainUiTabMethod

TAB_NAME = 'Roster'


class TabRosterAdapter:
    @MainUiTabMethod(TAB_NAME)
    @abc.abstractmethod
    def tab_roster_show_data_in_table(self):
        """"""
