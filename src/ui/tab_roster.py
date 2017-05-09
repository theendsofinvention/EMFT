# coding=utf-8

from utils import Path, ThreadPool, make_logger

from src.cfg import Config
from src.misc.fs import saved_games_path
from src.miz import Miz, Mission, parking_spots
from src.miz.mission import Group, FlyingUnit
from .base import TableView, TableProxy, TableModel, VLayout, HLayout, BrowseDialog, PushButton, \
    Label, HSpacer
from .itab import iTab
from .main_ui_interface import I
from .tab_roster_adapter import TAB_NAME
from .tab_roster_adapter import TabRosterAdapter

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

        self.miz_table = TableView()
        self.miz_model = TableModel(list(), ['Group name', 'Unit type', 'Livery', 'Position'])
        self.miz_proxy = TableProxy()

        self.miz_proxy.setSourceModel(self.miz_model)
        self.miz_table.setModel(self.miz_proxy)

        self.setLayout(
            VLayout(
                [
                    HLayout([self.load_miz_btn, self.miz_label, HSpacer()]),
                    self.miz_table
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

        parking_spots.clear_farps()
        for farp in self.miz.farps():
            parking_spots.add_farp(farp)

        data = []
        for group in self.miz.get_clients_groups():
            assert isinstance(group, Group)
            unit = group.first_unit()
            assert isinstance(unit, FlyingUnit)
            try:
                livery = unit.livery
            except KeyError:
                msg = 'no livery found for unit with id "{}" ("{}"), falling back to default'
                logger.error(msg.format(unit.unit_id, unit.unit_type))
                livery = '--default-- (no skin found for this A/C type)'

            line = [group.group_name, unit.unit_type, livery]

            start_pos = group.group_start_position
            # print(group.first_unit().unit_position)
            if start_pos == 'From Parking Area':
                start_pos = parking_spots.unit_pos_to_spot(group.first_unit().unit_position)

                if start_pos:
                    line.append('{start_pos.airport}: {start_pos.spot}'.format(start_pos=start_pos))
                else:
                    raise Exception(group.group_id)
            else:
                line.append(start_pos)

            data.append(line)

        if len(data) == 0:
            logger.error('no client group found in: {}'.format(self._miz_path.abspath()))
            self.main_ui.error('No client group found in this MIZ file.')

        self.miz_model.reset_data(data)
        self.miz_table.resizeColumnsToContents()

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
