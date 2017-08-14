# coding=utf-8

from emft.core import constant
from emft.core.logging import make_logger
from emft.gui.base import GridLayout, HSpacer, Label, VLayout, VSpacer
from emft.gui.main_ui_tab_widget import MainUiTabChild

LOGGER = make_logger(__name__)


class TabChildAbout(MainUiTabChild):
    def tab_clicked(self):
        pass

    @property
    def tab_title(self) -> str:
        return 'About'

    def __init__(self, parent=None):
        super(TabChildAbout, self).__init__(parent)

        repo_label = Label(
            '''<a href='{link}'>{link}</a>'''.format(link=constant.LINK_REPO)
        )
        repo_label.setOpenExternalLinks(True)

        changelog_label = Label(
            '''<a href='{link}'>{link}</a>'''.format(link=constant.LINK_CHANGELOG)
        )
        changelog_label.setOpenExternalLinks(True)

        self.setLayout(
            VLayout(
                [
                    GridLayout(
                        [
                            [Label('Github repository: '), repo_label, HSpacer()],
                            [Label('Changelog: '), changelog_label, HSpacer()],
                        ],
                        [0, 0, 1]
                    ),
                    VSpacer(),
                ]
            )
        )
