# coding=utf-8

from utils import make_logger

from src.misc import dcs_installs, DCSInstall, DCSSkin
from src.ui.base import VLayout, Combo, HLayout, Label, HSpacer, TableModel, TableView, TableProxy, LineEdit, GroupBox, \
    GridLayout
from src.ui.itab import iTab

logger = make_logger(__name__)


class TabSkins(iTab):
    @property
    def tab_title(self) -> str:
        return 'Skins'

    def __init__(self):
        super(TabSkins, self).__init__()

        self.no_install_label = Label('No DSC installation found on this system')
        self.no_install_label.set_text_color('red')
        self.no_install_label.setVisible(len(list(dcs_installs.present_dcs_installations)) == 0)

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

        data = []

        header_data = ['Skin name', 'Aircraft', 'Containing folder']

        self.table = TableView()
        self.model = TableModel(data, header_data)

        self.proxy = TableProxy()
        self.proxy.setSourceModel(self.model)
        # noinspection PyUnresolvedReferences
        self.model.modelReset.connect(self.proxy.default_sort)
        self.table.setModel(self.proxy)

        self.setLayout(
            VLayout(
                [
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
                                [Label('AC name:'), self.filter_ac_name, ],
                                [Label('Folder:'), self.filter_folder, ],
                            ]
                        ),
                    ),
                    (self.table, dict(stretch=1)),
                ],

            )
        )

    def _on_active_dcs_installation_change(self):
        def skin_to_data_line(skin: DCSSkin):
            return [skin.skin_nice_name, skin.ac, skin.root_folder]

        install = getattr(dcs_installs, self.combo_active_dcs_installation.currentText())
        assert isinstance(install, DCSInstall)
        install.discover_skins()
        self.model.reset_data(
            [skin_to_data_line(skin) for skin in install.skins.values()]
        )
        self.table.resizeColumnsToContents()

    def _apply_filter(self):
        self.proxy.filter(
            self.filter_skin_name.text(),
            self.filter_ac_name.text(),
            self.filter_folder.text(),
        )
