# coding=utf-8

import os

from utils import Path

from src.cfg import Config
from src.misc.dcs_installs import DCSInstalls
from src.ui.base import VLayout, PushButton, HLayout, GroupBox, LineEdit, Label, Spacer
from src.ui.dialog_browse import BrowseDialog
from src.ui.itab import iTab


class TabConfig(iTab):
    @property
    def tab_title(self) -> str:
        return 'Config'

    def __init__(self, parent=None):
        iTab.__init__(self, parent=parent)

        self.sg = LineEdit(Config().saved_games_path or '', self._on_change_sg, read_only=True)
        self.btn_sg_browse = PushButton('Browse', self._sg_browse)
        self.btn_sg_scan = PushButton('Scan', self._sg_scan)
        self.btn_sg_open = PushButton('Open', self._sg_open)
        sg_path_layout = HLayout(
            [
                (Label('"Saved Games" folder:'), dict(stretch=0)),
                (self.sg, dict(stretch=1)),
                self.btn_sg_browse,
                self.btn_sg_scan,
                self.btn_sg_open,
            ]
        )

        dcs_installations = []
        for x in ['stable', 'beta', 'alpha']:
            setattr(self, '{}_group'.format(x), GroupBox('DCS {} installation'.format(x)))
            setattr(self, '{}_install'.format(x), Label(''))
            setattr(self, '{}_variant'.format(x), Label(''))
            setattr(self, '{}_version'.format(x), Label(''))
            getattr(self, '{}_group'.format(x)).setLayout(
                VLayout(
                    [
                        HLayout([Label('Installation: '), (getattr(self, '{}_install'.format(x)), dict(stretch=1))]),
                        HLayout([Label('Variant: '), (getattr(self, '{}_variant'.format(x)), dict(stretch=1))]),
                        HLayout([Label('Version: '), (getattr(self, '{}_version'.format(x)), dict(stretch=1))]),
                    ]
                )
            )
            dcs_installations.append(getattr(self, '{}_group'.format(x)))

        dcs_installations = VLayout(
            [
                *dcs_installations
            ]
        )

        self.setLayout(
            VLayout(
                [
                    sg_path_layout,
                    dcs_installations,
                    Spacer(),
                ]
            )
        )

    def update_config_tab(self):
        for x in ['stable', 'beta', 'alpha']:
            getattr(self, '{}_install'.format(x)).setText(getattr(DCSInstalls(), x).install_path)
            getattr(self, '{}_variant'.format(x)).setText(getattr(DCSInstalls(), x).saved_games)
            getattr(self, '{}_version'.format(x)).setText(getattr(DCSInstalls(), x).version)

    def _on_change_sg(self):
        Config().saved_games_path = str(Path(self.sg.text()).abspath())

    def _sg_browse(self):
        p = BrowseDialog.get_directory(self, 'Saved Games directory', Path(self.sg.text()).dirname())
        if p:
            p = str(Path(p).abspath())
            self.sg.setText(p)

    def _sg_scan(self):
        self.sg.setText(DCSInstalls().discover_saved_games_path())

    def _sg_open(self):
        os.startfile(self.sg.text())
