# coding=utf-8

import os
import webbrowser

from utils import Path, Version, AVRelease, make_logger

from src import global_
from src.__version__ import __version__
from src.cfg import Config
from src.misc.dcs_installs import dcs_installs
from src.ui.base import VLayout, PushButton, GroupBox, LineEdit, Label, VSpacer, GridLayout, Combo, HSpacer, HLayout
from src.ui.dialog_browse import BrowseDialog
from src.ui.itab import iTab
from src.ui.main_ui_interface import I
from src.updater import updater

logger = make_logger(__name__)


class TabConfig(iTab):
    @property
    def tab_title(self) -> str:
        return 'Config'

    def __init__(self, parent=None):
        iTab.__init__(self, parent=parent)
        self.sg = LineEdit(Config().saved_games_path or '', self._on_change_sg, read_only=True)
        self.update_channel_combo = Combo(self._on_change_update_channel, ['stable', 'rc', 'dev'])

        self.latest_release = None

        self.remote_version = Label('')
        self.update_channel_combo.set_index_from_text(Config().update_channel)
        self.update_scan_btn = PushButton('Check for new version', self._check_for_new_version)
        self.show_changelog_btn = PushButton('Show changelog', self._show_changelog)
        self.install_new_version_btn = PushButton('Install this version', self._install_latest_version)

        updater_layout = GroupBox(
            'Auto-update',
            VLayout(
                [
                    Label('During the initial testing phase of this application, auto-update cannot be turned off.\n'
                          'You can, however, elect to participate in early testing, or stick to the most stable'
                          ' versions only.'),
                    20,
                    GridLayout(
                        [
                            [
                                Label('Active update channel'),
                                self.update_channel_combo,
                                self.update_scan_btn,
                                HSpacer(),
                                Label('Current version'),
                                Label(__version__),
                                self.show_changelog_btn,
                                HSpacer(),
                            ],
                            [
                                HSpacer(),
                                (Label('stable:'), {'align': 'r'}),
                                Label('tested releases'),
                                HSpacer(),
                                Label('Remote version'),
                                self.remote_version,
                                self.install_new_version_btn,
                                HSpacer(),
                            ],
                            [
                                HSpacer(),
                                (Label('rc:'), {'align': 'r'}),
                                Label('releases candidates'),
                                HSpacer(),
                                HSpacer(),
                                HSpacer(),
                                HSpacer(),
                                HSpacer(),
                            ],
                            [
                                HSpacer(),
                                (Label('dev:'), {'align': 'r'}),
                                Label('experimental versions'),
                                HSpacer(),
                                HSpacer(),
                                HSpacer(),
                                HSpacer(),
                                HSpacer(),
                            ],
                        ],
                        [0, 0, 0, 25, 0, 0, 0, 50]
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
        for x, y in [('stable', 'Stable'), ('beta', 'Open beta'), ('alpha', 'Open alpha')]:
            setattr(self, '{}_group'.format(x), GroupBox(y))
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
            dcs_installations.append(HSpacer())

        dcs_installations = GroupBox(
            'DCS Installations',
            HLayout(
                [
                    *dcs_installations[:-1]
                ]
            )
        )

        self.setLayout(
            VLayout(
                [
                    updater_layout,
                    VSpacer(),
                    sg_path_layout,
                    VSpacer(),
                    dcs_installations,
                    # VSpacer(),
                ]
            )
        )

        self.install_new_version_btn.setVisible(False)

    def _show_changelog(self):
        webbrowser.open_new_tab(global_.LINK_CHANGELOG)

    def update_config_tab(self, latest_release: AVRelease):
        self.remote_version.set_text_color('black')
        for x in ['stable', 'beta', 'alpha']:
            dcs_install = getattr(dcs_installs, x)
            if dcs_install:
                getattr(self, '{}_install'.format(x)).setText(dcs_install.install_path)
                getattr(self, '{}_variant'.format(x)).setText(dcs_install.saved_games)
                getattr(self, '{}_version'.format(x)).setText(dcs_install.version)
            else:
                getattr(self, '{}_install'.format(x)).setText('not found')
        self.update_channel_combo.set_index_from_text(Config().update_channel)
        if latest_release:
            app_version = Version(global_.APP_VERSION)
            self.latest_release = latest_release
            self.remote_version.setText(latest_release.version.version_str)
            if app_version < self.latest_release.version:
                self.remote_version.set_text_color('green')
            if app_version != self.latest_release.version:
                self.install_new_version_btn.setVisible(True)

    def _on_change_sg(self, *_):
        Config().saved_games_path = str(Path(self.sg.text()).abspath())

    def _on_change_update_channel(self, *_):
        Config().update_channel = self.update_channel_combo.currentText()
        self.remote_version.setText('')
        self._check_for_new_version()

    def _check_for_new_version(self):
        if hasattr(self, 'install_new_version_btn'):
            self.install_new_version_btn.setVisible(False)
        updater.get_latest_release(
            channel=Config().update_channel,
            branch=Version(global_.APP_VERSION),
            success_callback=I.update_config_tab,
        )

    def _install_latest_version(self):
        if self.latest_release:
            logger.debug('installing release: {}'.format(self.latest_release.version))
            updater.download_and_install_release(self.latest_release, 'emft.exe')
        else:
            logger.error('no release to install')
            # self.updater.install_latest_remote()

    def _sg_browse(self):
        p = BrowseDialog.get_directory(self, 'Saved Games directory', Path(self.sg.text()).dirname())
        if p:
            p = str(Path(p).abspath())
            self.sg.setText(p)

    def _sg_scan(self):
        self.sg.setText(dcs_installs.discover_saved_games_path())

    def _sg_open(self):
        os.startfile(self.sg.text())

    def stable_open(self):
        pass

    def alpha_open(self):
        pass

    def beta_open(self):
        pass
