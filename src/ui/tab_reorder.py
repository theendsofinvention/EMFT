# coding=utf-8

import abc
import os
import webbrowser
from distutils.version import LooseVersion

from PyQt5.QtWidgets import QLineEdit, QLabel
from natsort import natsorted
from utils.custom_logging import make_logger
from utils.custom_path import Path

from src.cfg.cfg import Config
from src.misc.fs import saved_games_path
from src.misc import appveyor, downloader, github
from src.miz.miz import Miz
from src.ui.base import GroupBox, HLayout, VLayout, PushButton, Radio, Checkbox, Label, Combo, GridLayout, VSpacer, \
    box_question, BrowseDialog
from src.ui.main_ui_tab_widget import MainUiTabChild
from src.ui.main_ui_interface import I
from .tab_reorder_adapter import TabReorderAdapter, TAB_NAME

try:
    import winreg
except ImportError:
    from unittest.mock import MagicMock

    winreg = MagicMock()

logger = make_logger(__name__)

A_REG = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


def get_saved_games_path():
    if Config().saved_games_path is None:
        logger.debug('searching for base "Saved Games" folder')
        try:
            logger.debug('trying "User Shell Folders"')
            with winreg.OpenKey(A_REG,
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as aKey:
                # noinspection SpellCheckingInspection
                base_sg = Path(winreg.QueryValueEx(aKey, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")[0])
        except FileNotFoundError:
            logger.debug('failed, trying "Shell Folders"')
            try:
                with winreg.OpenKey(A_REG,
                                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as aKey:
                    # noinspection SpellCheckingInspection
                    base_sg = Path(winreg.QueryValueEx(aKey, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")[0])
            except FileNotFoundError:
                logger.debug('darn it, another fail, falling back to "~"')
                base_sg = Path('~').expanduser().abspath()
        Config().saved_games_path = str(base_sg.abspath())
        return base_sg
    else:
        return Path(Config().saved_games_path)


class _SingleLayout:
    def __init__(self):

        self.single_group = GroupBox()

        self.single_miz = QLineEdit()
        self.single_miz.setDisabled(True)
        if Config().single_miz_last:
            p = Path(Config().single_miz_last)
            if p.exists() and p.isfile() and p.ext == '.miz':
                self.single_miz.setText(str(p.abspath()))

        self.single_miz_browse = PushButton('Browse', self.browse_for_single_miz)
        self.single_miz_open = PushButton('Open', self.open_single_miz)

        self.single_miz_output_folder = QLineEdit()
        self.single_miz_output_folder.setDisabled(True)
        if Config().single_miz_output_folder:
            p = Path(Config().single_miz_output_folder)
            self.single_miz_output_folder.setText(str(p.abspath()))

        self.single_miz_output_folder_browse = PushButton('Browse', self.browse_for_single_miz_output_folder)
        self.single_miz_output_folder_open = PushButton('Open', self.open_single_miz_output_folder)

        self.single_miz_reorder_btn = PushButton('Reorder MIZ file', self.single_reorder)
        self.single_miz_reorder_btn.setMinimumHeight(40)
        self.single_miz_reorder_btn.setMinimumWidth(400)

        self.single_layout = VLayout([
            GridLayout(
                [
                    [(Label('Source MIZ'), dict(align='r')), self.single_miz, self.single_miz_browse,
                     self.single_miz_open],
                    [(Label('Output folder'), dict(align='r')), self.single_miz_output_folder,
                     self.single_miz_output_folder_browse,
                     self.single_miz_output_folder_open],
                ],
            ),
            self.single_miz_reorder_btn,
        ])

        self.single_group.setLayout(self.single_layout)

    @property
    def single_miz_path(self) -> Path or None:
        t = self.single_miz.text()
        if len(t) > 3:
            p = Path(t)
            if p.exists() and p.isfile() and p.ext == '.miz':
                return p
        return None

    @property
    def single_miz_output_folder_path(self) -> Path or None:
        t = self.single_miz_output_folder.text()
        if len(t) > 3:
            return Path(t)
        return None

    def open_single_miz(self):
        if self.single_miz_path.exists():
            os.startfile(self.single_miz_path.dirname())

    def browse_for_single_miz(self):
        if Config().single_miz_last:
            init_dir = Path(Config().single_miz_last).dirname()
        else:
            init_dir = saved_games_path.abspath()
        p = BrowseDialog.get_existing_file(
            self, 'Select MIZ file', filter_=['*.miz'], init_dir=init_dir)
        if p:
            p = Path(p)
            self.single_miz.setText(p.abspath())
            Config().single_miz_last = p.abspath()

    def open_single_miz_output_folder(self):
        if self.single_miz_output_folder_path.exists():
            os.startfile(self.single_miz_output_folder_path)

    def browse_for_single_miz_output_folder(self):
        if self.single_miz_output_folder_path:
            init_dir = self.single_miz_output_folder_path.dirname()
        elif self.single_miz_path:
            init_dir = self.single_miz_path.dirname()
        else:
            init_dir = Path('.')
        p = BrowseDialog.get_directory(self, 'Select output directory', init_dir=init_dir.abspath())
        if p:
            p = Path(p)
            self.single_miz_output_folder.setText(p.abspath())
            Config().single_miz_output_folder = p.abspath()

    def single_reorder(self):
        if self.single_miz_path and self.single_miz_output_folder_path:
            self.reorder_miz(self.single_miz_path, self.single_miz_output_folder_path, self.skip_options_file)

    @abc.abstractmethod
    def reorder_miz(self, miz_file, output_dir, skip_options_file):
        """"""

    @property
    @abc.abstractmethod
    def skip_options_file(self) -> bool:
        """"""


class _AutoLayout:
    def __init__(self):

        self.auto_group = GroupBox()
        auto_help = QLabel('Looks for the latest TRMT MIZ (must be named "TRMT_*.miz") in the source folder.')

        self._latest_trmt_path = None

        self.auto_src_le = QLineEdit()
        if Config().auto_source_folder:
            self.auto_src_le.setText(Config().auto_source_folder)
        self.auto_src_le.setEnabled(False)
        self.auto_src_browse_btn = PushButton('Browse', self.auto_src_browse)
        self.auto_src_open_btn = PushButton('Open', self.auto_src_open)
        self.auto_scan_label_local = QLabel('')
        self.auto_scan_label_remote = Label('')
        self.auto_scan_combo_branch = Combo(self._branch_changed, ['All'] + github.get_available_branches())
        try:
            self.auto_scan_combo_branch.set_index_from_text(Config().selected_TRMT_branch)
        except ValueError:
            pass

        self.auto_scan_btn = PushButton('Refresh', self.scan)
        self.auto_scan_download_btn = PushButton('Download', self.auto_download)

        self.auto_out_le = QLineEdit()
        self.auto_out_le.setEnabled(False)
        self.auto_out_browse_btn = PushButton('Browse', self.auto_out_browse)
        self.auto_out_open_btn = PushButton('Open', self.auto_out_open)

        scan_layout = HLayout([
            QLabel('Latest local version of the TRMT:'),
            (self.auto_scan_label_local, dict(stretch=1)),
            QLabel('Latest remote version of the TRMT:'),
            self.auto_scan_combo_branch,
            (self.auto_scan_label_remote, dict(stretch=1)),
        ])

        self.auto_reorder_btn = PushButton('Reorder MIZ file', self.auto_reorder)
        self.auto_reorder_btn.setMinimumHeight(40)
        self.auto_reorder_btn.setMinimumWidth(400)

        self.auto_layout = VLayout([

            auto_help,

            GridLayout(
                [
                    [
                        (Label('Source folder'), dict(align='r')),
                        self.auto_src_le,
                        self.auto_src_browse_btn,
                        self.auto_src_open_btn,
                    ],
                    [
                        (Label('Output folder'), dict(align='r')),
                        self.auto_out_le,
                        self.auto_out_browse_btn,
                        self.auto_out_open_btn,
                    ],
                    [
                        None,
                        scan_layout,
                        self.auto_scan_btn,
                        self.auto_scan_download_btn
                    ],
                ]
            ),
            self.auto_reorder_btn
        ])

        self.auto_group.setLayout(self.auto_layout)

        if Config().auto_output_folder:
            self.auto_out_le.setText(Config().auto_output_folder)
        if Config().auto_source_folder:
            self.auto_src_le.setText(Config().auto_source_folder)

    @abc.abstractmethod
    def _branch_changed(self):
        """"""

    def auto_reorder(self):
        if self.latest_trmt and self.auto_out_path:
            self.reorder_miz(self.latest_trmt, self.auto_out_path, self.skip_options_file)

    def auto_out_open(self):
        if self.auto_out_path.exists():
            os.startfile(str(self.auto_out_path))

    def auto_out_browse(self):
        if self.auto_out_path:
            init_dir = self.auto_out_path.dirname()
        else:
            init_dir = Path('.')
        p = BrowseDialog.get_directory(self, 'Select output directory', init_dir=init_dir.abspath())
        if p:
            p = Path(p)
            self.auto_out_le.setText(p.abspath())
            Config().auto_output_folder = p.abspath()

    @property
    def auto_out_path(self) -> Path or None:
        t = self.auto_out_le.text()
        if len(t) > 3:
            return Path(t)
        return None

    @property
    @abc.abstractmethod
    def selected_branch(self):
        """"""

    @abc.abstractmethod
    def scan(self):
        """"""

    @staticmethod
    def get_av_token():
        # noinspection SpellCheckingInspection
        webbrowser.open_new_tab(r'https://ci.appveyor.com/api-token')

    @abc.abstractmethod
    def auto_download(self):
        """"""

    @property
    def auto_src_path(self) -> Path or None:
        t = self.auto_src_le.text()
        if len(t) > 3:
            return Path(t)
        return None

    def auto_src_browse(self):
        if self.auto_src_path:
            init_dir = self.auto_src_path.dirname()
        else:
            init_dir = saved_games_path
        p = BrowseDialog.get_directory(self, 'Select source directory', init_dir=init_dir.abspath())
        if p:
            p = Path(p)
            self.auto_src_le.setText(p.abspath())
            Config().auto_source_folder = p.abspath()
            self.scan()

    def auto_src_open(self):
        if self.auto_src_path:
            os.startfile(str(self.auto_src_path.abspath()))

    @property
    def latest_trmt(self) -> Path or None:
        return self._latest_trmt_path

    @abc.abstractmethod
    def reorder_miz(self, miz_file, output_dir, skip_options_file):
        """"""

    @property
    @abc.abstractmethod
    def skip_options_file(self) -> bool:
        """"""


class TabChildReorder(MainUiTabChild, _SingleLayout, _AutoLayout, TabReorderAdapter):
    def tab_clicked(self):
        self.scan()

    @property
    def tab_title(self):
        return TAB_NAME

    def __init__(self, parent=None):
        MainUiTabChild.__init__(self, parent=parent)
        _SingleLayout.__init__(self)
        _AutoLayout.__init__(self)

        self._remote = None
        self.local_version = None

        help_text = QLabel('By design, LUA tables are unordered, which makes tracking changes extremely difficult.\n\n'
                           'This lets you reorder them alphabetically before you push them in a SCM.\n\n'
                           'It is recommended to set the "Output folder" to your local SCM repository.')

        self.check_skip_options = Checkbox(
            'Skip "options" file: the "options" file at the root of the MIZ is player-specific, and is of very relative'
            ' import for the MIZ file itself. To avoid having irrelevant changes in the SCM, it can be safely skipped'
            ' during reordering.',
            self.toggle_skip_options
        )

        self.radio_single = Radio('Specific MIZ file', self.toggle_radios)
        self.radio_auto = Radio('Latest TRMT', self.toggle_radios)

        self.setLayout(
            VLayout(
                [
                    help_text,

                    GroupBox(
                        'Options',
                        VLayout([self.check_skip_options, ])
                    ),

                    40,

                    self.radio_single, self.single_group,

                    self.radio_auto, self.auto_group,

                    VSpacer()
                ]
            )
        )

        self.radio_single.setChecked(not Config().auto_mode)
        self.radio_auto.setChecked(Config().auto_mode)
        self.check_skip_options.setChecked(Config().skip_options_file)
        self.toggle_radios()

    def toggle_skip_options(self, *_):
        Config().skip_options_file = self.check_skip_options.isChecked()

    def toggle_radios(self, *_):
        self.single_group.setEnabled(self.radio_single.isChecked())
        self.auto_group.setEnabled(self.radio_auto.isChecked())
        Config().auto_mode = self.radio_auto.isChecked()

    @property
    def skip_options_file(self) -> bool:
        return self.check_skip_options.isChecked()

    @staticmethod
    def _on_reorder_error(miz_file):
        # noinspection PyCallByClass
        I.error('Could not unzip the following file:\n\n{}\n\n'
                'Please check the log, and eventually send it to me along with the MIZ file '
                'if you think this is a bug.'.format(miz_file))

    def reorder_miz(self, miz_file, output_dir, skip_options_file):
        self.main_ui.pool.queue_task(
            Miz.reorder,
            [
                miz_file,
                output_dir,
                skip_options_file,
            ],
            _err_callback=self._on_reorder_error,
            _err_args=[miz_file],
        )

    @property
    def selected_branch(self):
        return self.auto_scan_combo_branch.currentText()

    def _branch_changed(self):
        Config().selected_TRMT_branch = self.selected_branch
        self.scan()

    def tab_reorder_update_view_after_remote_scan(self):
        if self.local_version:
            self.auto_scan_label_local.setText(self.local_version)
        else:
            self.auto_scan_label_local.setText('No TRMT local MIZ file found.')

        if self.remote:
            self.auto_scan_label_remote.setText('{} ({})'.format(self.remote.version, self.remote.branch))
            logger.debug('latest remote TRMT found: {}'.format(self.remote.version))
            if self.local_version:
                if LooseVersion(self.local_version) < LooseVersion(self.remote.version):
                    self.auto_scan_label_remote.set_text_color('green')
                    logger.debug('remote TRMT is newer than local')
                else:
                    logger.debug('no new TRMT version found')
            else:
                self.auto_scan_label_remote.set_text_color('green')

    def __scan_local(self):

        if self.auto_src_path:
            try:
                logger.debug('looking for latest local TRMT version')
                self._latest_trmt_path = natsorted(
                    [Path(f).abspath() for f in Path(self.auto_src_path).listdir('TRMT_*.miz')]).pop()
            except IndexError:
                self._latest_trmt_path = None
                self.local_version = None
                logger.debug('no local TRMT found')
            else:
                self.local_version = Path(self._latest_trmt_path).namebase.replace('TRMT_', '')
                logger.debug('latest local TRMT found: {}'.format(self.local_version))

    def __scan_remote(self):

        # noinspection PyBroadException
        try:
            logger.debug('looking for latest remote TRMT version')
            self._remote = appveyor.get_latest_remote_version(self.selected_branch)
        except:
            logger.debug('no remote TRMT found')
            self._remote = None

    def _scan(self):
        if self.auto_src_path:
            self.__scan_local()
            self.__scan_remote()

    @staticmethod
    def _scan_callback(*_):
        I.tab_reorder_update_view_after_remote_scan()

    def scan(self, *_):
        self.auto_scan_label_remote.set_text_color('black')
        self.auto_scan_label_remote.setText('Probing...')
        self.auto_scan_label_local.setText('Probing...')
        self.main_ui.pool.queue_task(task=self._scan, _task_callback=self._scan_callback)

    @property
    def remote(self) -> appveyor.AVResult:
        return self._remote

    def auto_download(self):

        if self.remote:
            local_file = Path(self.auto_src_path).joinpath(self.remote.file_name).abspath()

            if local_file.exists():
                if not box_question(self, 'Local file already exists; do you want to overwrite?'):
                    return

            self.main_ui.pool.queue_task(
                downloader.download,
                kwargs=dict(
                    url=self.remote.download_url,
                    local_file=local_file,
                    progress_title='Downloading {}'.format(self.remote.download_url.split('/').pop()),
                    progress_text=self.remote.file_name,
                    file_size=self.remote.file_size
                ),
                _task_callback=self.scan
            )
