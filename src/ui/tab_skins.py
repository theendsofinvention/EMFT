# coding=utf-8
import os
import re

from utils import make_logger

from src.cfg import Config
from src.misc.dcs_installs import dcs_installs, DCSInstall, DCSSkin
from src.ui.base import VLayout, Combo, HLayout, Label, HSpacer, TableModel, TableViewWithSingleRowMenu, \
    TableProxy, LineEdit, GroupBox, GridLayout, Menu, Checkbox
from src.ui.itab import iTab

logger = make_logger(__name__)

RE_MOUNT_LINE = re.compile(r'^mount_vfs_texture_path\("(?P<path>.*)"\)\n$')
RE_LOAD_MODEL_LINE = re.compile(r'^LoadModel\("(?P<path>.*)"\)$')
RE_LOAD_LIVERY_LINE = re.compile(r'^LoadLivery\("(?P<path>.*)"\)$')


class TabSkins(iTab):
    @property
    def tab_title(self) -> str:
        return 'Skins'

    def __init__(self, parent=None):
        super(TabSkins, self).__init__(parent)

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
            self._on_active_dcs_installation_change,
            list(x.label for x in dcs_installs.present_dcs_installations),
        )

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

    def _display_list_of_skins_for_currently_selected_install(self):
        def skin_to_data_line(skin: DCSSkin):
            return [skin.skin_nice_name, skin.ac, skin.root_folder]

        if self._active_dcs_install:
            self.model.reset_data(
                [skin_to_data_line(skin) for skin in self._active_dcs_install.skins.values()]
            )
            self.table.resizeColumnsToContents()

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
