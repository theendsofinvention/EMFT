# coding=utf-8

from emft.utils import make_logger

from emft import global_
from emft.ui.base import VLayout, Label, HSpacer, GridLayout, VSpacer
from emft.ui.main_ui_tab_widget import MainUiTabChild

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
            '''<a href='{link}'>{link}</a>'''.format(link=global_.LINK_REPO)
        )
        repo_label.setOpenExternalLinks(True)

        changelog_label = Label(
            '''<a href='{link}'>{link}</a>'''.format(link=global_.LINK_CHANGELOG)
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
