# coding=utf-8

from utils import make_logger

from src import global_
from src.cfg import Config
from src.sentry import SENTRY
from src.ui.base import PlainTextEdit
from src.ui.base import GroupBox, VLayout, Combo, HLayout, Label, HSpacer, VSpacer, TableModel, TableView, TableProxy
from src.ui.itab import iTab
from src.ui.main_ui_interface import I
from src.misc import dcs_installs, DCSInstall, DCSSkin

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


