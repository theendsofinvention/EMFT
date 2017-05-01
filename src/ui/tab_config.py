# coding=utf-8

import os
import webbrowser

from utils import Path, Version, AVRelease, make_logger

from src import global_
from src.__version__ import __version__
from src.cfg import Config
from src.misc.fs import dcs_installs, saved_games
from src.ui.base import VLayout, PushButton, GroupBox, LineEdit, Label, VSpacer, GridLayout, Combo, HSpacer, HLayout, \
    BrowseDialog
from src.ui.main_ui_tab_widget import MainUiTabChild
from src.ui.main_ui_interface import I
from src.updater import updater
from .tab_config_adapter import TAB_NAME, TabConfigAdapter

logger = make_logger(__name__)


class TabChildConfig(MainUiTabChild, TabConfigAdapter):

    def tab_clicked(self):
        self._check_for_new_version()
        self._sg_scan()

    @property
    def tab_title(self) -> str:
        return TAB_NAME

    def __init__(self, parent=None):
        MainUiTabChild.__init__(self, parent=parent)
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
        for x, y in [('stable', 'Stable'), ('beta', 'Open beta'), ('alpha', 'Open alpha'), ('custom', 'Custom')]:
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
            # dcs_installations.append(HSpacer())

        self.custom_dcs_install_install_set = PushButton('Set', self._custom_dcs_install_set)
        self.custom_dcs_install_install_remove = PushButton('Remove', self._custom_dcs_install_remove)

        dcs_installations = GroupBox(
            'DCS Installations',
            GridLayout([
                [HLayout([dcs_installations[0]]), HLayout([dcs_installations[1]])],
                [HLayout([dcs_installations[2]]), HLayout([dcs_installations[3]])],
                [
                    HSpacer(),
                    HLayout(
                        [
                            Label('Custom DCS installation:'),
                            self.custom_dcs_install_install_set,
                            self.custom_dcs_install_install_remove,
                            HSpacer()
                        ]
                    )
                ]
                # HLayout([*dcs_installations[0:2]]),
                # HLayout([*dcs_installations[2:]]),
            ]),
            # HLayout(
            #     [
            #         *dcs_installations[:-1]
            #     ]
            # )
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

        self.install_new_version_btn.setVisible(False)

    def _custom_dcs_install_set(self):
        logger.debug('setting custom DCS install')
        install_dir = BrowseDialog.get_directory(self, 'DCS installation directory')
        if not install_dir:
            logger.debug('user cancelled')
            return
        variant = BrowseDialog.get_directory(self, 'Variant directory (DCS subdir in Saved Games)',
                                             init_dir=saved_games.saved_games_path)
        if not variant:
            logger.debug('user cancelled')
            return
        dcs_installs.add_custom(install_dir, variant)

    @staticmethod
    def _custom_dcs_install_remove():
        dcs_installs.remove_custom()

    @staticmethod
    def _show_changelog():
        webbrowser.open_new_tab(global_.LINK_CHANGELOG)

    def config_tab_update_dcs_installs(self):
        self.remote_version.set_text_color('black')
        for x in ['stable', 'beta', 'alpha', 'custom']:
            dcs_install = getattr(dcs_installs, x)
            if dcs_install:
                getattr(self, '{}_install'.format(x)).setText(dcs_install.install_path)
                getattr(self, '{}_variant'.format(x)).setText(dcs_install.saved_games)
                getattr(self, '{}_version'.format(x)).setText(dcs_install.version)
            else:
                getattr(self, '{}_install'.format(x)).setText('not found')
                getattr(self, '{}_variant'.format(x)).setText('')
                getattr(self, '{}_version'.format(x)).setText('')
        self.update_channel_combo.set_index_from_text(Config().update_channel)
        self.custom_dcs_install_install_remove.setEnabled(bool(Config().dcs_custom_install_path))

    def config_tab_update_latest_release(self, latest_release: AVRelease):
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
        self.remote_version.setText('Probing ...')
        updater.get_latest_release(
            channel=Config().update_channel,
            branch=Version(global_.APP_VERSION),
            success_callback=I.config_tab_update_latest_release,
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
        saved_games.discover_saved_games_path()
        self.sg.setText(saved_games.saved_games_path)

    def _sg_open(self):
        os.startfile(self.sg.text())

    def stable_open(self):
        pass

    def alpha_open(self):
        pass

    def beta_open(self):
        pass
