# coding=utf-8

import os

from utils import Path
from utils import Updater

from src import global_
from src.__version__ import __version__, __guid__
from src.cfg import Config
from src.misc.dcs_installs import DCSInstalls
from src.ui.base import VLayout, PushButton, GroupBox, LineEdit, Label, VSpacer, GridLayout, Combo, HLayout, HSpacer
from src.ui.dialog_browse import BrowseDialog
from src.ui.itab import iTab
from src.ui.main_ui_interface import I


class TabConfig(iTab):
    @property
    def tab_title(self) -> str:
        return 'Config'

    def __init__(self, parent=None):
        iTab.__init__(self, parent=parent)
        self.sg = LineEdit(Config().saved_games_path or '', self._on_change_sg, read_only=True)
        self.update_channel_combo = Combo(self._on_change_update_channel, [
            'stable', 'rc', 'dev', 'beta', 'alpha'
        ])

        self.updater = Updater(
            **global_.UPDATER_CONFIG,
            auto_update=False,
            channel=Config().update_channel
        )

        self.update_channel_combo.set_index_from_text(Config().update_channel)
        self.update_scan_btn = PushButton('Check for new version', self._check_for_new_version)
        self.install_new_version = PushButton('Install latest version', self._check_for_new_version)
        self.remote_version = Label('')

        updater_layout = GroupBox(
            'Auto-update',
            VLayout(
                [
                    Label('During the initial testing phase of this application, auto-update cannot be turned off.\n'
                          'You can, however, elect to participate in early testing, or stick to the most stable'
                          ' versions only.'),
                    10,
                    GridLayout(
                        [
                            [
                                Label('Active update channel'), HLayout(
                                    [
                                        self.update_channel_combo,
                                        self.update_scan_btn,
                                        HSpacer()
                                    ]
                            ),
                            ],
                            [10],
                            [
                                Label('Current version'),
                                (Label(__version__), dict(span=[1, -1])),
                            ],
                            [
                                Label('Remote version'),
                                (self.remote_version, dict(span=[1, -1])),
                            ],
                            [
                                Label('GUID'),
                                (Label(__guid__), dict(span=[1, -1])),
                            ],
                        ],
                        [0, 1]
                    )
                ]
            )
        )

        sg_path_layout = GroupBox(
            'Saved Games directory',
            GridLayout(
                [
                    [
                        self.sg,
                        PushButton('Browse', self._sg_browse),
                        PushButton('Scan', self._sg_scan),
                        PushButton('Open', self._sg_open),
                    ]
                ],
                [1],
                False
            )
        )

        dcs_installations = []
        for x in ['stable', 'beta', 'alpha']:
            setattr(self, '{}_group'.format(x), GroupBox('DCS {} installation'.format(x)))
            setattr(self, '{}_install'.format(x), Label(''))
            setattr(self, '{}_variant'.format(x), Label(''))
            setattr(self, '{}_version'.format(x), Label(''))
            getattr(self, '{}_group'.format(x)).setLayout(
                GridLayout(
                    [
                        [Label('Installation'), getattr(self, '{}_install'.format(x)), ],
                        [Label('Variant'), getattr(self, '{}_variant'.format(x))],
                        [Label('Version'), getattr(self, '{}_version'.format(x))],
                    ],
                    [0, 1]
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
                    updater_layout,
                    VSpacer(),
                    sg_path_layout,
                    VSpacer(),
                    dcs_installations,
                    VSpacer(),
                ]
            )
        )

    def update_config_tab(self, version_check_result):
        for x in ['stable', 'beta', 'alpha']:
            getattr(self, '{}_install'.format(x)).setText(getattr(DCSInstalls(), x).install_path)
            getattr(self, '{}_variant'.format(x)).setText(getattr(DCSInstalls(), x).saved_games)
            getattr(self, '{}_version'.format(x)).setText(getattr(DCSInstalls(), x).version)
        self.update_channel_combo.set_index_from_text(Config().update_channel)
        if version_check_result:
            latest_remote, new_version_available = version_check_result
            if new_version_available:
                self.remote_version.set_text_color('green')
            else:
                self.remote_version.set_text_color('black')
            self.remote_version.setText(latest_remote)

    def _on_change_sg(self, *_):
        Config().saved_games_path = str(Path(self.sg.text()).abspath())

    def _on_change_update_channel(self, *_):
        Config().update_channel = self.update_channel_combo.currentText()
        self.remote_version.setText('')
        self._check_for_new_version()

    def _check_for_new_version(self):
        self.updater.channel = Config().update_channel
        self.updater.get_latest_remote(I.update_config_tab)

    def _install_latest_version(self):
        self.updater.install_latest_remote()

    def _sg_browse(self):
        p = BrowseDialog.get_directory(self, 'Saved Games directory', Path(self.sg.text()).dirname())
        if p:
            p = str(Path(p).abspath())
            self.sg.setText(p)

    def _sg_scan(self):
        self.sg.setText(DCSInstalls().discover_saved_games_path())

    def _sg_open(self):
        os.startfile(self.sg.text())

    def stable_open(self):
        pass

    def alpha_open(self):
        pass

    def beta_open(self):
        pass
