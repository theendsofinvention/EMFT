# coding=utf-8
import os
import re

from emft.config import Config
from emft.core.filesystem import DCSInstall, dcs_installs
from emft.core.logging import make_logger
from emft.gui.base import Checkbox, Combo, GridLayout, GroupBox, HLayout, HSpacer, Label, LineEdit, Menu, PushButton, \
    TableModel, TableProxy, TableViewWithSingleRowMenu, VLayout
from emft.gui.main_ui_tab_widget import MainUiTabChild
from emft.gui.tab_skins_adapter import TAB_NAME, TabSkinsAdapter

LOGGER = make_logger(__name__)

RE_MOUNT_LINE = re.compile(r'^mount_vfs_texture_path\("(?P<path>.*)"\)\n$')
RE_LOAD_MODEL_LINE = re.compile(r'^LoadModel\("(?P<path>.*)"\)$')
RE_LOAD_LIVERY_LINE = re.compile(r'^LoadLivery\("(?P<path>.*)"\)$')


class TabChildSkins(MainUiTabChild, TabSkinsAdapter):
    def tab_clicked(self):
        self._refresh_skins_for_active_install()

    def tab_skins_update_dcs_installs_combo(self):
        with self.combo_active_dcs_installation:
            self.combo_active_dcs_installation.clear()
            self.combo_active_dcs_installation.addItems(list(x.label for x in dcs_installs.present_dcs_installations))
        try:
            self.combo_active_dcs_installation.set_index_from_text(Config().skins_active_dcs_installation)
        except ValueError:
            with self.combo_active_dcs_installation:
                self.combo_active_dcs_installation.setCurrentIndex(0)

    @property
    def tab_title(self) -> str:
        return TAB_NAME

    def __init__(self, parent=None):
        super(TabChildSkins, self).__init__(parent)

        self.no_install_label = Label('No DSC installation found on this system')
        self.no_install_label.set_text_color('red')
        self.no_install_label.setVisible(len(list(dcs_installs.present_dcs_installations)) == 0)

        self.allow_mv_autoexec_changes = Checkbox(
            'Allow EMFT to edit the "autoexec.cfg" of DCS ModelViewer to inject required VFS textures paths',
            self._on_allow_mv_autoexec_changes,
        )
        self.allow_mv_autoexec_changes.setChecked(Config().allow_mv_autoexec_changes)

        def _make_filter():
            return LineEdit(
                '',
                on_text_changed=self._apply_filter,
                clear_btn_enabled=True
            )

        self.filter_skin_name = _make_filter()
        self.filter_ac_name = _make_filter()
        self.filter_folder = _make_filter()

        self.combo_active_dcs_installation = Combo(
            self._on_active_dcs_installation_change
        )

        self.refresh_skins_btn = PushButton('Refresh skins list', self._refresh_skins_for_active_install)

        for x in {self.combo_active_dcs_installation, self.refresh_skins_btn}:
            x.setVisible(len(list(dcs_installs.present_dcs_installations)) > 0)

        if Config().skins_active_dcs_installation:
            try:
                self.combo_active_dcs_installation.set_index_from_text(Config().skins_active_dcs_installation)
            except ValueError:
                pass

        data = []

        header_data = ['Skin name', 'Aircraft', 'Containing folder']

        self._menu = Menu('Title')
        # self._menu.add_action('Test menu', self._test_menu)
        self._menu.add_action('Open skin folder', self._context_open_folder)
        # self._menu.add_action('Show skin in model viewer', self._show_skin_in_model_viewer)

        self.table = TableViewWithSingleRowMenu(self._menu)
        self.table.setSelectionMode(self.table.SingleSelection)
        # noinspection PyUnresolvedReferences
        self.table.doubleClicked.connect(self._table_double_clicked)
        self.model = TableModel(data, header_data)

        self.proxy = TableProxy()
        self.proxy.setSourceModel(self.model)
        # noinspection PyUnresolvedReferences
        self.model.modelReset.connect(self.proxy.default_sort)
        self.table.setModel(self.proxy)

        self.setLayout(
            VLayout(
                [
                    # self.allow_mv_autoexec_changes,
                    HLayout(
                        [
                            Label('Active DCS installation:'),
                            self.combo_active_dcs_installation,
                            self.refresh_skins_btn,
                            self.no_install_label,
                            HSpacer(),
                        ]
                    ),
                    GroupBox(
                        'Filters',
                        GridLayout(
                            [
                                [Label('Skin name:'), self.filter_skin_name, ],
                                [Label('Aircraft:'), self.filter_ac_name, ],
                                [Label('Folder:'), self.filter_folder, ],
                            ]
                        ),
                    ),
                    (self.table, dict(stretch=1)),
                ],

            )
        )

        self._display_list_of_skins_for_currently_selected_install()

    def _table_double_clicked(self, index):
        if index.isValid():
            self._context_open_folder(index.row())

    def _context_open_folder(self, row):
        os.startfile(self.proxy.data(self.proxy.index(row, 2)))

    def _refresh_skins_for_active_install(self):
        if self._active_dcs_install:
            self._active_dcs_install.discover_skins()
            self._display_list_of_skins_for_currently_selected_install()

    # def _show_skin_in_model_viewer(self, row):
    #     skin_name = self.proxy.data(self.proxy.index(row, 0))
    #     ac_name = self.proxy.data(self.proxy.index(row, 1))
    #     mv_autoexec_cfg = Path(self._active_dcs_install.install_path).joinpath(
    #         'Config', 'ModelViewer', 'autoexec.lua'
    #     )
    #     mv_exe = Path(self._active_dcs_install.install_path).joinpath(
    #         'bin', 'ModelViewer.exe'
    #     )
    #
    #     for f in mv_autoexec_cfg, mv_exe:
    #         if not f.exists():
    #             logger.error('file not found: {}'.format(f.abspath()))
    #             return
    #
    #     mount_lines = set()
    #     if self._active_dcs_install.autoexec_cfg:
    #         for vfs_path in self._active_dcs_install.autoexec_cfg.mounted_vfs_paths:
    #             mount_lines.add('mount_vfs_texture_path("{}")\n'.format(vfs_path))
    #
    #     backup_path = mv_autoexec_cfg.dirname().joinpath('autoexec.lua_EMFT_BACKUP')
    #     if not backup_path.exists():
    #         logger.info('backing up "{}" -> "{}"'.format(mv_autoexec_cfg.abspath(), backup_path.abspath()))
    #         mv_autoexec_cfg.copy2(backup_path.abspath())
    #
    #     orig_lines = mv_autoexec_cfg.lines()
    #
    #     lines = []
    #
    #     for line in orig_lines:
    #         if Config().allow_mv_autoexec_changes:
    #             if RE_MOUNT_LINE.match(line):
    #                 # print('skipping', line)
    #                 continue
    #         if RE_LOAD_MODEL_LINE.match(line):
    #             # print('skipping', line)
    #             continue
    #         if RE_LOAD_LIVERY_LINE.match(line):
    #             # print('skipping', line)
    #             continue
    #         lines.append(line)
    #
    #     # model_path = 'LoadModel("Bazar/World/Shapes/{}.edm")'.format(
    #           self._active_dcs_install.get_object_model(ac_name))
    #
    #     lines.insert(0, 'LoadLivery("{ac_name}","{skin_name}")'.format(**locals()))
    #     lines.insert(0, 'LoadModel("Bazar/World/Shapes/{ac_name}.edm")'.format(**locals()))
    #
    #     if Config().allow_mv_autoexec_changes:
    #         for line in mount_lines:
    #             lines.insert(0, line)
    #
    #     mv_autoexec_cfg.write_lines(lines)
    #
    #     os.startfile(mv_exe.abspath())

    def _test_menu(self, row):
        print(self.proxy.data(self.proxy.index(row, 0)))

    @property
    def _active_dcs_install(self) -> DCSInstall:
        if self.combo_active_dcs_installation.currentText():
            return getattr(dcs_installs, self.combo_active_dcs_installation.currentText())

    def tab_skins_show_skins_scan_result(self, scan_result):
        self.model.reset_data(scan_result)
        self.table.resizeColumnsToContents()

    def _display_list_of_skins_for_currently_selected_install(self):

        # def gather_data():
        #     return [
        #         [skin.skin_nice_name, skin.ac, skin.root_folder]
        #         for skin in self._active_dcs_install.skins.values()
        #     ]

        if self._active_dcs_install:
            pass

            # TODO: find another way to call a common thread pool
            # self.main_ui.pool.queue_task(
            #     task=gather_data,
            #     _task_callback=I.tab_skins_show_skins_scan_result
            # )

            # self.model.reset_data(
            #     [skin_to_data_line(skin) for skin in self._active_dcs_install.skins.values()]
            # )
            # self.table.resizeColumnsToContents()

    def _on_active_dcs_installation_change(self):
        Config().skins_active_dcs_installation = self.combo_active_dcs_installation.currentText()
        self._display_list_of_skins_for_currently_selected_install()

    def _apply_filter(self):
        self.proxy.filter(
            self.filter_skin_name.text(),
            self.filter_ac_name.text(),
            self.filter_folder.text(),
        )

    def _on_allow_mv_autoexec_changes(self):
        Config().allow_mv_autoexec_changes = self.allow_mv_autoexec_changes.isChecked()
