# coding=utf-8

import os

from utils.custom_logging import make_logger
from utils.custom_path import Path

from src.cfg.cfg import Config
from src.global_ import MAIN_UI
from src.misc import appveyor, downloader, github_old
from src.misc.fs import saved_games_path
from src.miz.miz import Miz
from src.ui.base import GroupBox, HLayout, VLayout, PushButton, Radio, Checkbox, Label, Combo, GridLayout, box_question, \
    BrowseDialog, LineEdit
from src.ui.main_ui_interface import I
from src.ui.main_ui_tab_widget import MainUiTabChild
from .tab_reorder_adapter import TabReorderAdapter, TAB_NAME

try:
    import winreg
except ImportError:
    from unittest.mock import MagicMock

    winreg = MagicMock()

logger = make_logger(__name__)


class TabChildReorder(MainUiTabChild, TabReorderAdapter):
    def tab_clicked(self):
        self.scan_artifacts()

    @property
    def tab_title(self):
        return TAB_NAME

    def __init__(self, parent=None):
        MainUiTabChild.__init__(self, parent=parent)

        self.manual_group = GroupBox()

        self.single_miz_lineedit = LineEdit('', read_only=True)

        self.manual_output_folder_lineedit = LineEdit('', read_only=True)

        self.auto_src_le = LineEdit('', read_only=True)

        self.auto_scan_label_result = Label('')
        self.auto_scan_combo_branch = Combo(self._on_branch_changed, list())

        self.auto_out_le = LineEdit('', read_only=True)

        self._remote = None

        self.check_skip_options = Checkbox(
            'Skip "options" file: the "options" file at the root of the MIZ is player-specific, and is of very relative'
            ' import for the MIZ file itself. To avoid having irrelevant changes in the SCM, it can be safely skipped'
            ' during reordering.',
            self.toggle_skip_options
        )

        self.radio_single = Radio('Manual mode', self.on_radio_toggle)
        self.radio_auto = Radio('Automatic mode', self.on_radio_toggle)

        self.setLayout(
            VLayout(
                [
                    Label(
                        'By design, LUA tables are unordered, which makes tracking changes extremely difficult.\n\n'
                        'This lets you reorder them alphabetically before you push them in a SCM.\n\n'
                        'It is recommended to set the "Output folder" to your local SCM repository.'
                    ), 20,
                    GroupBox(
                        'Options',
                        VLayout(
                            [
                                self.check_skip_options,
                            ],
                        )
                    ), 20,
                    GroupBox(
                        'MIZ file reordering',
                        GridLayout(
                            [
                                [
                                    (self.radio_single, dict(span=(1, -1))),
                                ],
                                [
                                    Label('Source MIZ'),
                                    self.single_miz_lineedit,
                                    PushButton('Browse', self.manual_browse_for_miz, self),
                                    PushButton('Open', self.manual_open_miz, self),
                                ],
                                [
                                    Label('Output folder'),
                                    self.manual_output_folder_lineedit,
                                    PushButton('Browse', self.manual_browse_for_output_folder, self),
                                    PushButton('Open', self.manual_open_output_folder, self),
                                ],
                                [
                                    (self.radio_auto, dict(span=(1, -1))),
                                ],
                                [
                                    Label('Source folder'),
                                    self.auto_src_le,
                                    PushButton('Browse', self.auto_src_browse, self),
                                    PushButton('Open', self.auto_src_open, self),
                                ],
                                [
                                    Label('Output folder'),
                                    self.auto_out_le,
                                    PushButton('Browse', self.auto_out_browse, self),
                                    PushButton('Open', self.auto_out_open, self),
                                ],
                                [
                                    Label('Branch filter'),
                                    HLayout(
                                        [
                                            self.auto_scan_combo_branch,
                                            self.auto_scan_label_result,
                                        ],
                                    ),
                                    PushButton('Refresh', self.scan_artifacts, self),
                                    PushButton('Download', self.auto_download, self)
                                ],
                            ],
                        ),
                    ), 20,
                    PushButton(
                        text='Reorder MIZ file',
                        func=self.reorder_miz,
                        parent=self,
                        min_height=40,
                    ),
                ],
                set_stretch=[(4, 2)]
            )
        )
        self._initialize_config_values()
        # self.scan_branches()
        # self.scan_artifacts()
        self.initial_scan()

    def _initialize_config_values(self):
        self.radio_single.setChecked(not Config().auto_mode)
        self.radio_auto.setChecked(Config().auto_mode)
        self.check_skip_options.setChecked(Config().skip_options_file)
        if Config().auto_source_folder:
            self.auto_src_le.setText(Config().auto_source_folder)

        if Config().single_miz_last:
            p = Path(Config().single_miz_last)
            if p.exists() and p.isfile() and p.ext == '.miz':
                self.single_miz_lineedit.setText(str(p.abspath()))

        if Config().single_miz_output_folder:
            p = Path(Config().single_miz_output_folder)
            self.manual_output_folder_lineedit.setText(str(p.abspath()))

        if Config().auto_output_folder:
            p = Path(Config().auto_output_folder)
            if p.exists() and p.isdir():
                self.auto_out_le.setText(Config().auto_output_folder)

        if Config().auto_source_folder:
            p = Path(Config().auto_source_folder)
            if p.exists() and p.isdir():
                self.auto_src_le.setText(Config().auto_source_folder)

    @property
    def manual_miz_path(self) -> Path or None:
        t = self.single_miz_lineedit.text()
        if len(t) > 3:
            p = Path(t)
            if p.exists() and p.isfile() and p.ext == '.miz':
                return p
        return None

    @property
    def manual_output_folder_path(self) -> Path or None:
        t = self.manual_output_folder_lineedit.text()
        if len(t) > 3:
            return Path(t)
        return None

    def manual_open_miz(self):
        if self.manual_miz_path.exists():
            os.startfile(self.manual_miz_path.dirname())

    def manual_browse_for_miz(self):
        if Config().single_miz_last:
            init_dir = Path(Config().single_miz_last).dirname()
        else:
            init_dir = saved_games_path.abspath()
        p = BrowseDialog.get_existing_file(
            self, 'Select MIZ file', filter_=['*.miz'], init_dir=init_dir)
        if p:
            p = Path(p)
            self.single_miz_lineedit.setText(p.abspath())
            Config().single_miz_last = p.abspath()

    def manual_open_output_folder(self):
        if self.manual_output_folder_path and self.manual_output_folder_path.exists():
            os.startfile(self.manual_output_folder_path)

    def manual_browse_for_output_folder(self):
        if self.manual_output_folder_path:
            init_dir = self.manual_output_folder_path.dirname()
        elif self.manual_miz_path:
            init_dir = self.manual_miz_path.dirname()
        else:
            init_dir = Path('.')
        p = BrowseDialog.get_directory(self, 'Select output directory', init_dir=init_dir.abspath())
        if p:
            p = Path(p)
            self.manual_output_folder_lineedit.setText(p.abspath())
            Config().single_miz_output_folder = p.abspath()

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
            self.scan_artifacts()

    def auto_src_open(self):
        if self.auto_src_path:
            os.startfile(str(self.auto_src_path.abspath()))

    def toggle_skip_options(self, *_):
        Config().skip_options_file = self.check_skip_options.isChecked()

    def on_radio_toggle(self, *_):
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

    def reorder_miz(self):
        if self.radio_auto.isChecked():
            if self.remote and self.auto_out_path:
                local_file = self._look_for_local_file(self.remote.version)
                self._reorder_miz(local_file, self.auto_out_path, self.skip_options_file)
        else:
            if self.manual_miz_path and self.manual_output_folder_path:
                self._reorder_miz(self.manual_miz_path, self.manual_output_folder_path, self.skip_options_file)

    def _reorder_miz(self, miz_file, output_dir, skip_options_file):
        if miz_file:
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
        else:
            MAIN_UI.msg('Local file not found for version: {}\n\n'
                        'Download it first!'.format(self.remote.version))

    @property
    def selected_branch(self):
        return self.auto_scan_combo_branch.currentText()

    def _on_branch_changed(self):
        Config().reorder_selected_auto_branch = self.selected_branch
        self.scan_artifacts()

    def tab_reorder_update_view_after_branches_scan(self, *_):

        try:
            self.auto_scan_combo_branch.set_index_from_text(Config().reorder_selected_auto_branch)
        except ValueError:
            MAIN_UI.msg('Selected branch has been deleted from the remote:\n\n{}'.format(
                Config().reorder_selected_auto_branch))
            self.auto_scan_combo_branch.setCurrentIndex(0)

    def tab_reorder_update_view_after_artifact_scan(self, *_):

        if self.remote:

            if isinstance(self.remote, str):
                # The scan returned an error message
                msg, color = self.remote, 'red'

            else:

                # self.auto_scan_label_result.setText('{} ({})'.format(self.remote.version, self.remote.branch))
                logger.debug('latest remote version found: {}'.format(self.remote.version))
                local_trmt_path = self._look_for_local_file(self.remote.version)
                if local_trmt_path:
                    msg, color = '{}: you have the latest version'.format(self.remote.version), 'green'
                    logger.debug(msg)
                    self.auto_scan_label_result.setText(msg)
                else:
                    msg, color = '{}: new version found'.format(self.remote.version), 'orange'
                    logger.debug(msg)
        else:
            msg, color = 'error while probing remote, see log', 'red'

        self.auto_scan_label_result.setText(msg)
        self.auto_scan_label_result.set_text_color(color)

    def _look_for_local_file(self, version):

        if self.auto_src_path:
            p = Path(self.auto_src_path).joinpath('TRMT_{}.miz'.format(version))
            if p.exists():
                logger.debug('local TRMT found: {}'.format(p.abspath()))
                return p.abspath()
            else:
                logger.warning('no local MIZ file found with version: {}'.format(self.remote.version))
                return None

    def _initial_scan(self):
        self.tab_reorder_update_view_after_artifact_scan(self._scan_branches())
        self._scan_artifacts()

    def initial_scan(self):
        self.main_ui.pool.queue_task(self._initial_scan)

    def _scan_branches(self):
        remote_branches = github_old.get_available_branches()
        remote_branches.remove('master')
        remote_branches.remove('develop')
        self.auto_scan_combo_branch.reset_values(
            ['All', 'master', 'develop'] + sorted(remote_branches)
        )

    def scan_branches(self, *_):
        self.main_ui.pool.queue_task(
            task=self._scan_branches,
            _task_callback=I.tab_reorder_update_view_after_branches_scan
        )

    def _scan_artifacts(self):
        if self.auto_src_path:
            # noinspection PyBroadException
            try:
                logger.debug('looking for latest remote TRMT version')
                self._remote = appveyor.get_latest_remote_version(self.selected_branch)
            except:
                logger.debug('no remote TRMT found')
                self._remote = None

    def scan_artifacts(self, *_):
        self.auto_scan_label_result.set_text_color('black')
        self.auto_scan_label_result.setText('Probing...')
        self.main_ui.pool.queue_task(
            task=self._scan_artifacts,
            _task_callback=I.tab_reorder_update_view_after_artifact_scan)

    @property
    def remote(self) -> appveyor.AVResult:
        return self._remote

    def auto_download(self):

        if self.remote and not isinstance(self.remote, str):
            local_file = Path(self.auto_src_path).joinpath(self.remote.file_name).abspath()

            if local_file.exists():
                if not box_question(self, 'Local file already exists; do you want to overwrite?'):
                    return

            MAIN_UI.progress_start(
                'Downloading {}'.format(self.remote.download_url.split('/').pop()),
                length=100,
                label=self.remote.file_name
            )

            self.main_ui.pool.queue_task(
                downloader.download,
                kwargs=dict(
                    url=self.remote.download_url,
                    local_file=local_file,
                    file_size=self.remote.file_size
                ),
                _task_callback=self.scan_artifacts
            )
