# coding=utf-8

from PyQt5.QtWidgets import QTabWidget
from .itab import iTab


class MainUiTabWidget(QTabWidget):

    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self._tabs = []
        # noinspection PyUnresolvedReferences
        self.currentChanged.connect(self._current_index_changed)

    def addTab(self, tab: iTab, *__args):
        self._tabs.append(tab)
        super(MainUiTabWidget, self).addTab(tab, *__args)

    def _current_index_changed(self, tab_index):
        self._tabs[tab_index].tab_clicked()