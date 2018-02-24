# coding=utf-8

import os
import webbrowser

from emft.__version__ import __version__
from emft.config import Config
from emft.core import constant
from emft.core.filesystem import dcs_installs, saved_games
from emft.core.logging import make_logger
from emft.core.path import Path
from emft.gui.base import BrowseDialog, Combo, GridLayout, GroupBox, HLayout, HSpacer, Label, LineEdit, PushButton, \
    VLayout, VSpacer
from emft.gui.main_ui_interface import I
from emft.gui.main_ui_tab_widget import MainUiTabChild
from emft.gui.tab_config_adapter import TAB_NAME, TabConfigAdapter
from emft.updater import channel, customversion, updater

LOGGER = make_logger(__name__)


class TabChildConfig(MainUiTabChild, TabConfigAdapter):
    def tab_clicked(self):
        pass
        # # if updater.updateris_ready:
        # #     self._check_for_new_version()
        # self._sg_scan()

    @property
    def tab_title(self) -> str:
        return TAB_NAME

    def __init__(self, parent=None):
        MainUiTabChild.__init__(self, parent=parent)
        # self.sg = LineEdit(Config().saved_games_path or '', self._on_change_sg, read_only=True)
        self.update_channel_combo = Combo(
            self._on_change_update_channel,
            channel.LABELS
        )

        self.latest_version = None

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
                          ' versions only.\n\n'
                          'If you want, you can use this tab to "force" the installation of an older version.'),
                    20,
                    GridLayout(
                        [
                            [
                                Label('Active update channel'),
                                self.update_channel_combo,
                            ],
                            [
                                HSpacer(),
                                self.update_scan_btn,
                            ],
                            [
                                HSpacer(),
                                GridLayout(
                                    [
                                        [
                                            HSpacer(),
                                            (Label('stable:'), {'align': 'r'}),
                                            Label('tested releases and patches'),
                                        ],
                                        [
                                            HSpacer(),
                                            (Label('patches:'), {'align': 'r'}),
                                            Label('testing version of upcoming hotfixes'),
                                        ],
                                        [
                                            HSpacer(),
                                            (Label('rc:'), {'align': 'r'}),
                                            Label('releases candidates (tagged "exp")'),
                                        ],
                                        [
                                            HSpacer(),
                                            (Label('beta:'), {'align': 'r'}),
                                            Label('development branch'),
                                        ],
                                        [
                                            HSpacer(),
                                            (Label('alpha:'), {'align': 'r'}),
                                            Label('unstable versions'),
                                        ],
                                    ],
                                ),
                            ],
                            [
                                Label('Current version'),
                                Label(__version__),
                            ],
                            [
                                Label('Remote version'),
                                self.remote_version,
                            ],
                            [
                                HSpacer(),
                                self.install_new_version_btn,
                            ],
                            [
                                HSpacer(),
                                self.show_changelog_btn,
                            ],
                        ],
                        [0, 0, 0, 25, 0, 0, 0, 50]
                    ),
                ]
            )
        )

        # # sg_path_layout = GroupBox(
        # #     'Saved Games directory',
        # #     GridLayout(
        # #         [
        # #             [
        # #                 self.sg,
        # #                 PushButton('Browse', self._sg_browse),
        # #                 PushButton('Scan', self._sg_scan),
        # #                 PushButton('Open', self._sg_open),
        # #             ]
        # #         ],
        # #         [1],
        # #         False
        # #     )
        # # )
        #
        # dcs_installations = []
        # for x, y in [('stable', 'Stable'), ('beta', 'Open beta'), ('alpha', 'Open alpha'), ('custom', 'Custom')]:
        #     setattr(self, '{}_group'.format(x), GroupBox(y))
        #     setattr(self, '{}_install'.format(x), Label(''))
        #     setattr(self, '{}_variant'.format(x), Label(''))
        #     setattr(self, '{}_version'.format(x), Label(''))
        #     getattr(self, '{}_group'.format(x)).setLayout(
        #         GridLayout(
        #             [
        #                 [Label('Installation'), getattr(self, '{}_install'.format(x)), ],
        #                 [Label('Variant'), getattr(self, '{}_variant'.format(x))],
        #                 [Label('Version'), getattr(self, '{}_version'.format(x))],
        #             ],
        #             [0, 1]
        #         )
        #     )
        #     dcs_installations.append(getattr(self, '{}_group'.format(x)))
        #     # dcs_installations.append(HSpacer())
        #
        # self.custom_dcs_install_install_set = PushButton('Set', self._custom_dcs_install_set)
        # self.custom_dcs_install_install_remove = PushButton('Remove', self._custom_dcs_install_remove)
        #
        # dcs_installations = GroupBox(
        #     'DCS Installations',
        #     GridLayout([
        #         [HLayout([dcs_installations[0]]), HLayout([dcs_installations[1]])],
        #         [HLayout([dcs_installations[2]]), HLayout([dcs_installations[3]])],
        #         [
        #             HSpacer(),
        #             HLayout(
        #                 [
        #                     Label('Custom DCS installation:'),
        #                     self.custom_dcs_install_install_set,
        #                     self.custom_dcs_install_install_remove,
        #                     HSpacer()
        #                 ]
        #             )
        #         ]
        #         # HLayout([*dcs_installations[0:2]]),
        #         # HLayout([*dcs_installations[2:]]),
        #     ]),
        #     # HLayout(
        #     #     [
        #     #         *dcs_installations[:-1]
        #     #     ]
        #     # )
        # )
        self.setLayout(
            VLayout(
                [
                    updater_layout,
                    # VSpacer(),
                    # sg_path_layout,
                    # VSpacer(),
                    # dcs_installations,
                    # VSpacer(),
                ]
            )
        )

        self.install_new_version_btn.setEnabled(False)
        updater.Updater.latest_version.add_watcher(self._display_new_version)
        updater.Updater.is_ready.add_watcher(self._updater_ready_to_check)
        self.update_scan_btn.setEnabled(updater.updater.is_ready)

    # def _custom_dcs_install_set(self):
    #     LOGGER.debug('setting custom DCS install')
    #     install_dir = BrowseDialog.get_directory(self, 'DCS installation directory')
    #     if not install_dir:
    #         LOGGER.debug('user cancelled')
    #         return
    #     variant = BrowseDialog.get_directory(self, 'Variant directory (DCS subdir in Saved Games)',
    #                                          init_dir=saved_games.saved_games_path)
    #     if not variant:
    #         LOGGER.debug('user cancelled')
    #         return
    #     dcs_installs.add_custom(install_dir, variant)
    #
    # @staticmethod
    # def _custom_dcs_install_remove():
    #     dcs_installs.remove_custom()

    @staticmethod
    def _show_changelog():
        webbrowser.open_new_tab(constant.LINK_CHANGELOG)

    def _updater_ready_to_check(self, value: bool):
        self.update_scan_btn.setEnabled(value)

    def _display_new_version(self, latest_version: customversion.CustomVersion):
        """
        Shows the latest version found by the updater
        """
        if latest_version:
            app_version = customversion.CustomVersion(__version__)
            self.latest_version = latest_version
            self.remote_version.setText(latest_version.to_short_string())
            if app_version < self.latest_version:
                self.remote_version.set_text_color('green')
            if app_version != self.latest_version:
                self.install_new_version_btn.setEnabled(True)
        else:
            self.remote_version.setText('no new version found')

    # def config_tab_update_dcs_installs(self):
    #     self.remote_version.set_text_color('black')
    #     for x in ['stable', 'beta', 'alpha', 'custom']:
    #         dcs_install = getattr(dcs_installs, x)
    #         if dcs_install:
    #             getattr(self, '{}_install'.format(x)).setText(dcs_install.install_path)
    #             getattr(self, '{}_variant'.format(x)).setText(dcs_install.saved_games)
    #             getattr(self, '{}_version'.format(x)).setText(dcs_install.version)
    #         else:
    #             getattr(self, '{}_install'.format(x)).setText('not found')
    #             getattr(self, '{}_variant'.format(x)).setText('')
    #             getattr(self, '{}_version'.format(x)).setText('')
    #     self.update_channel_combo.set_index_from_text(Config().update_channel)
    #     self.custom_dcs_install_install_remove.setEnabled(bool(Config().dcs_custom_install_path))

    # def _on_change_sg(self, *_):
    #     Config().saved_games_path = str(Path(self.sg.text()).abspath())

    def _on_change_update_channel(self, *_):
        Config().update_channel = self.update_channel_combo.currentText()

    def _check_for_new_version(self):
        if hasattr(self, 'install_new_version_btn'):
            self.install_new_version_btn.setEnabled(False)
        self.remote_version.set_text_color('black')
        updater.updater.find_latest_version_on_channel(
            channel.LABEL_TO_CHANNEL[self.update_channel_combo.currentText()]
        )

    def _install_latest_version(self):
        if updater.updater.latest_version:
            LOGGER.debug('installing release: {}'.format(self.latest_version))
            if updater.updater.latest_version < customversion.CustomVersion(__version__):
                I.confirm(
                    text='You are update to install an older version of EMFT.\n\nAre you sure?',
                    follow_up_on_yes=updater.updater.install_latest_version
                )
            else:
                updater.updater.install_latest_version()
        else:
            LOGGER.error('no release to install')
            # self.updater.updater.install_latest_remote()

    # def _sg_browse(self):
    #     p = BrowseDialog.get_directory(self, 'Saved Games directory', Path(self.sg.text()).dirname())
    #     if p:
    #         p = str(Path(p).abspath())
    #         self.sg.setText(p)
    #
    # def _sg_scan(self):
    #     saved_games.discover_saved_games_path()
    #     self.sg.setText(saved_games.saved_games_path)
    #
    # def _sg_open(self):
    #     os.startfile(self.sg.text())
    #
    # def stable_open(self):
    #     pass
    #
    # def alpha_open(self):
    #     pass
    #
    # def beta_open(self):
    #     pass
