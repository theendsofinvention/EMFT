# coding=utf-8
import os
import re

from utils import make_logger

from src.ui.base import VLayout, Combo, HLayout, Label, HSpacer, TableModel, TableViewWithSingleRowMenu, \
    TableProxy, LineEdit, GroupBox, GridLayout, Menu, Checkbox
from src.ui.itab import iTab

logger = make_logger(__name__)


class TabAbout(iTab):
    @property
    def tab_title(self) -> str:
        return 'About'

    def __init__(self, parent=None):
        super(TabAbout, self).__init__(parent)

        repo_label = Label(
            '''<a href='https://github.com/132nd-etcher/EMFT'>https://github.com/132nd-etcher/EMFT</a>'''
        )
        repo_label.setOpenExternalLinks(True)

        self.setLayout(
            GridLayout(
                [
                    [Label('Github repository: '), repo_label, HSpacer()]
                ],
                [0, 0, 1]
            )
        )