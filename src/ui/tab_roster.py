# coding=utf-8

from .itab import iTab
from .tab_roster_adapter import TAB_NAME
from .base import TableView, TableProxy, TableModel, GridLayout, VLayout, HLayout, BrowseDialog, LineEdit, PushButton,\
    Label, HSpacer
from src.misc.fs import saved_games_path
from src.miz.miz import Miz, Mission
from src.miz.mission import Group, FlyingUnit
from src.cfg import Config
from .main_ui_interface import I
from utils import Path, ThreadPool, make_logger


logger = make_logger(__name__)


class TabRoster(iTab, TabRosterAdapter):
    def tab_clicked(self):
        pass

    @property
    def tab_title(self):
        return TAB_NAME

    def __init__(self, parent=None):
        iTab.__init__(self, parent)

        self.load_miz_btn = PushButton('Load MIZ file', self._load_miz)
        self.miz_label = Label('No MIZ file loaded')
        self._miz = None
        self._miz_path = None

        self.table = TableView()
        self.model = TableModel(list(), ['Group name', 'Unit type', 'Livery'])
        self.proxy = TableProxy()

        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)

        self.setLayout(
            VLayout(
                [
                    HLayout([self.load_miz_btn, self.miz_label, HSpacer()]),
                    self.table
                ]
            )
        )

        self._last_dir = Config().roster_last_dir if \
            Config().roster_last_dir and Path(Config().roster_last_dir).exists() else None

        self.pool = ThreadPool(1, 'roster_tab', True)

    @property
    def miz(self) -> Mission:
        return self._miz

    def tab_roster_show_miz_in_table(self, *_):
        data = []
        for group in self.miz.get_clients_groups():
            assert isinstance(group, Group)
            unit = group.first_unit()
            assert isinstance(unit, FlyingUnit)
            try:
                livery = unit.livery
            except KeyError:
                msg = 'no livery found for unit with "{}" ("{}"), falling back to default'
                logger.error(msg.format(unit.unit_id, unit.unit_type))
                livery = 'Default'
            data.append([group.group_name, unit.unit_type, livery])

        if len(data) == 0:
            logger.error('no client group found in: {}'.format(self._miz_path.abspath()))
            self.main_ui.error('No client group found in this MIZ file.')

        self.model.reset_data(data)
        self.table.resizeColumnsToContents()

    def _load_miz(self):
        miz = BrowseDialog.get_existing_file(
            self,
            'Select MIZ file',
            _filter=['*.miz'],
            init_dir=self._last_dir or saved_games_path.abspath())

        if not miz:
            return

        self._miz_path = miz

        self._last_dir = str(miz.dirname())
        Config().roster_last_dir = self._last_dir
        self.miz_label.setText(miz.abspath())

        def decode_miz():
            with Miz(miz.abspath()) as m:
                self._miz = m.mission

        self.pool.queue_task(
            task=decode_miz,
            _task_callback=I.tab_roster_show_miz_in_table
        )
