# coding=utf-8

import abc
import os
import webbrowser
from distutils.version import LooseVersion

from PyQt5.QtWidgets import QLineEdit, QSpacerItem, QSizePolicy, QLabel
from natsort import natsorted
from utils.custom_logging import make_logger
from utils.custom_path import Path
from utils.threadpool import ThreadPool

from src.cfg.cfg import Config
from src.misc import appveyor, downloader
from src.miz.miz import Miz
from src.ui.base import GroupBox, HLayout, VLayout, PushButton, Radio, Checkbox, Label
from src.ui.dialog_browse import BrowseDialog
from src.ui.itab import iTab

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

        single_miz_path_layout = HLayout([
            QLabel('Source MIZ: '),
            (self.single_miz, dict(stretch=1)),
            (self.single_miz_browse, dict(stretch=0)),
            (self.single_miz_open, dict(stretch=0)),
        ])

        single_miz_output_layout = HLayout([
            QLabel('Output folder: '),
            (self.single_miz_output_folder, dict(stretch=1)),
            (self.single_miz_output_folder_browse, dict(stretch=0)),
            (self.single_miz_output_folder_open, dict(stretch=0)),

        ])

        self.single_miz_reorder_btn = PushButton('Reorder MIZ file', self.single_reorder)
        self.single_miz_reorder_btn.setMinimumHeight(40)
        self.single_miz_reorder_btn.setMinimumWidth(400)

        single_miz_btn_layout = HLayout([
            self.single_miz_reorder_btn
        ])

        self.single_layout = VLayout([
            single_miz_path_layout,
            single_miz_output_layout,
            QSpacerItem(1, 10, QSizePolicy.Expanding, QSizePolicy.Expanding),
            single_miz_btn_layout,
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
        init_dir = get_saved_games_path()
        p = BrowseDialog.get_existing_file(self, 'Select MIZ file', _filter=['*.miz'], init_dir=init_dir.abspath())
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

        self._latest_trmt = None

        self.auto_src_le = QLineEdit()
        if Config().auto_source_folder:
            self.auto_src_le.setText(Config().auto_source_folder)
        self.auto_src_le.setEnabled(False)
        self.auto_src_browse_btn = PushButton('Browse', self.auto_src_browse)
        self.auto_src_open_btn = PushButton('Open', self.auto_src_open)

        auto_folder_layout = HLayout([
            QLabel('Source folder:'),
            self.auto_src_le,
            self.auto_src_browse_btn,
            self.auto_src_open_btn,
        ])

        # scan_layout.setContentsMargins(source_folder_label.width(), 0, 0, 0)
        self.auto_scan_label_local = QLabel('')
        self.auto_scan_label_remote = Label('')
        # self.scan_label.setMinimumWidth(self.auto_folder_path.width())
        self.auto_scan_btn = PushButton('Refresh', self.scan)
        self.auto_scan_download_btn = PushButton('Download', self.download)

        self.auto_out_le = QLineEdit()
        self.auto_out_le.setEnabled(False)
        self.auto_out_browse_btn = PushButton('Browse', self.auto_out_browse)
        self.auto_out_open_btn = PushButton('Open', self.auto_out_open)

        output_layout = HLayout([
            QLabel('Output folder: '),
            (self.auto_out_le, dict(stretch=1)),
            (self.auto_out_browse_btn, dict(stretch=0)),
            (self.auto_out_open_btn, dict(stretch=0)),
        ])

        scan_layout = HLayout([
            QLabel('Latest local version of the TRMT:'),
            (self.auto_scan_label_local, dict(stretch=1)),
            QLabel('Latest remote version of the TRMT:'),
            (self.auto_scan_label_remote, dict(stretch=1)),
            self.auto_scan_btn,
            self.auto_scan_download_btn,
        ])

        self.auto_reorder_btn = PushButton('Reorder MIZ file', self.auto_reorder)
        self.auto_reorder_btn.setMinimumHeight(40)
        self.auto_reorder_btn.setMinimumWidth(400)
        auto_btn_layout = HLayout([
            self.auto_reorder_btn
        ])

        self.auto_layout = VLayout([
            20,
            auto_help,
            40,
            auto_folder_layout,
            output_layout,
            scan_layout,
            auto_btn_layout
        ])

        self.auto_group.setLayout(self.auto_layout)

        if Config().auto_output_folder:
            self.auto_out_le.setText(Config().auto_output_folder)
        if Config().auto_source_folder:
            self.auto_src_le.setText(Config().auto_source_folder)

    def auto_reorder(self):
        if self.latest_trmt and self.auto_out_path:
            self.reorder_miz(self.latest_trmt, self.auto_out_path, self.skip_options_file)

    def auto_out_open(self):
        if self.auto_out_path.exists():
            os.startfile(self.auto_out_path)

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

    @abc.abstractmethod
    def scan(self):
        """"""

    @property
    @abc.abstractmethod
    def pool(self) -> ThreadPool:
        """"""

    @staticmethod
    def get_av_token():
        # noinspection SpellCheckingInspection
        webbrowser.open_new_tab(r'https://ci.appveyor.com/api-token')

    def _download(self):
        dl_url, local_file_name = appveyor.latest_version_download_url()
        local_file = Path(self.auto_src_path).joinpath(local_file_name).abspath()
        downloader.download(dl_url, local_file, 'Downloading {}'.format(local_file))

    def download(self):
        self.pool.queue_task(self._download)
        self.scan()

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
            init_dir = get_saved_games_path()
        p = BrowseDialog.get_directory(self, 'Select source directory', init_dir=init_dir.abspath())
        if p:
            p = Path(p)
            self.auto_src_le.setText(p.abspath())
            Config().auto_source_folder = p.abspath()
            self.scan()

    def auto_src_open(self):
        if self.auto_src_path:
            os.startfile(self.auto_src_path.abspath())

    @property
    def latest_trmt(self) -> Path or None:
        return self._latest_trmt

    @abc.abstractmethod
    def reorder_miz(self, miz_file, output_dir, skip_options_file):
        """"""

    @property
    @abc.abstractmethod
    def skip_options_file(self) -> bool:
        """"""


class TabReorder(iTab, _SingleLayout, _AutoLayout):
    def __init__(self, parent=None):
        iTab.__init__(self, parent=parent)
        _SingleLayout.__init__(self)
        _AutoLayout.__init__(self)

        self._pool = ThreadPool(_basename='REORDER', _num_threads=1, _daemon=True)

        help_text = QLabel('By design, LUA tables are unordered, which makes tracking changes extremely difficult.\n\n'
                           'This lets you reorder them alphabetically before you push them in a SCM.\n\n'
                           'It is recommended to set the "Output folder" to your local SCM repository.')

        self.check_skip_options = Checkbox('Skip "options" file', self.toggle_skip_options)
        skip_options_help_text = QLabel(
            'The "options" file at the root of the MIZ is player-specific, and is of very relative import for the MIZ'
            ' file itself. To avoid having irrelevant changes in the SCM, it can be safely skipped during reordering.')

        self.radio_single = Radio('Specific MIZ file', self.toggle_radios)
        self.radio_auto = Radio('Latest TRMT', self.toggle_radios)

        layout = VLayout([
            QSpacerItem(1, 10, QSizePolicy.Expanding, QSizePolicy.Expanding),
            help_text,
            QSpacerItem(1, 10, QSizePolicy.Expanding, QSizePolicy.Expanding),
            self.check_skip_options,
            skip_options_help_text,
            QSpacerItem(1, 10, QSizePolicy.Expanding, QSizePolicy.Expanding),
            self.radio_single,
            self.single_group,
            QSpacerItem(1, 10, QSizePolicy.Expanding, QSizePolicy.Expanding),
            self.radio_auto,
            self.auto_group,
            QSpacerItem(1, 10, QSizePolicy.Expanding, QSizePolicy.Expanding),
        ])

        self.setLayout(layout)

        self.radio_single.setChecked(not Config().auto_mode)
        self.radio_auto.setChecked(Config().auto_mode)
        self.check_skip_options.setChecked(Config().skip_options_file)
        self.toggle_radios()
        self.scan()

    @property
    def pool(self) -> ThreadPool:
        return self._pool

    def toggle_skip_options(self, *_):
        Config().skip_options_file = self.check_skip_options.isChecked()

    def toggle_radios(self, *_):
        self.single_group.setEnabled(self.radio_single.isChecked())
        self.auto_group.setEnabled(self.radio_auto.isChecked())
        Config().auto_mode = self.radio_auto.isChecked()

    @property
    def tab_title(self):
        return 'Reorder lua tables'

    @property
    def skip_options_file(self) -> bool:
        return self.check_skip_options.isChecked()

    def reorder_miz(self, miz_file, output_dir, skip_options_file):
        self.pool.queue_task(
            Miz.reorder,
            [
                miz_file,
                output_dir,
                skip_options_file,
            ]
        )

    def _scan(self):

        self.auto_scan_label_remote.set_text_color('black')
        self.auto_scan_label_remote.setText('Probing...')

        if self.auto_src_path:
            try:
                self._latest_trmt = natsorted(
                    [Path(f).abspath() for f in Path(self.auto_src_path).listdir('TRMT_*.miz')]).pop()
            except IndexError:
                self._latest_trmt = None
                local_version = None
                self.auto_scan_label_local.setText('No TRMT local MIZ file found.')
            else:
                local_version = Path(self._latest_trmt).namebase.replace('TRMT_', '')
                self.auto_scan_label_local.setText(local_version)

            try:
                remote_version, remote_branch = appveyor.get_latest_remote_version()
                self.auto_scan_label_remote.setText('{} ({})'.format(remote_version, remote_branch))
            except:
                remote_version = None

            if remote_version:
                if local_version:
                    if LooseVersion(local_version) < LooseVersion(remote_version):
                        self.auto_scan_label_remote.set_text_color('green')
                else:
                    self.auto_scan_label_remote.set_text_color('green')

    def scan(self):

        self.pool.queue_task(task=self._scan)
