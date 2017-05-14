# coding=utf-8

import typing

from utils import Path, ThreadPool, make_logger

from src.cfg import Config
from src.misc.fs import saved_games_path
from src.miz import Miz, Mission, parking_spots
from src.miz.mission import Group, FlyingUnit
from src.roster import Roster
from src.ui.main_ui_tab_widget import MainUiTabChild
from .base import TableView, TableProxy, TableModel, VLayout, HLayout, BrowseDialog, PushButton, \
    Label, HSpacer, VSpacer
from .main_ui_interface import I
from .tab_roster_adapter import TAB_NAME
from .tab_roster_adapter import TabRosterAdapter

logger = make_logger(__name__)


class TabChildRoster(MainUiTabChild, TabRosterAdapter):
    def tab_clicked(self):
        pass

    @property
    def tab_title(self):
        return TAB_NAME

    def __init__(self, parent=None):
        MainUiTabChild.__init__(self, parent)

        self.roster = Roster()

        self.miz_data = []
        self.roster_data = []

        self._miz = None
        self._miz_path = None

        self.load_miz_btn = PushButton('Load MIZ file', self._load_miz)
        self.save_miz_btn = PushButton('Save MIZ file', self._save_miz)
        self.miz_label = Label('No MIZ file loaded')

        self.load_roster_btn = PushButton('Load roster file', self._load_roster)
        self.save_roster_btn = PushButton('Save roster file', self._save_roster)
        self.roster_label = Label('No roster file loaded')

        headers = ['Group name', 'Unit type', 'Livery']

        self.miz_table = TableView()
        self.miz_model = TableModel(list(), headers)
        self.miz_proxy = TableProxy()

        self.miz_proxy.setSourceModel(self.miz_model)
        self.miz_table.setModel(self.miz_proxy)

        self.roster_table = TableView()
        self.roster_table.setSortingEnabled(False)
        self.roster_model = TableModel(list(), headers)
        self.roster_model._data = self.roster
        self.roster_proxy = TableProxy()

        self.roster_proxy.setSourceModel(self.roster_model)
        self.roster_table.setModel(self.roster_proxy)

        self.transfer_right_btn = PushButton('>', self._transfer_right)

        self.setLayout(
            VLayout(
                [
                    HLayout(
                        [
                            VLayout(
                                [
                                    HLayout([self.load_miz_btn, self.save_miz_btn, HSpacer()]),
                                    self.miz_label,
                                    self.miz_table
                                ]
                            ),
                            VLayout(
                                [
                                    VSpacer(),
                                    self.transfer_right_btn,
                                    VSpacer(),
                                ]
                            ),
                            VLayout(
                                [
                                    HLayout([self.load_roster_btn, self.save_roster_btn, HSpacer()]),
                                    self.roster_label,
                                    self.roster_table
                                ]
                            ),
                        ]
                    )
                ]
            )
        )

        self._miz_last_dir = Config().roster_miz_last_dir if \
            Config().roster_miz_last_dir and Path(Config().roster_miz_last_dir).exists() else None

        self._roster_last_dir = Config().roster_roster_last_dir if \
            Config().roster_roster_last_dir and Path(Config().roster_roster_last_dir).exists() else None

        self.pool = ThreadPool(1, 'roster_tab', True)

    @property
    def selected_left(self) -> typing.Generator[Roster.Pilot, None, None]:
        indexes = self.miz_table.selectedIndexes()
        while indexes:
            idx = indexes[:3]
            indexes = indexes[3:]
            pilot_name = self.miz_model.data(idx[0])
            aircraft = self.miz_model.data(idx[1])
            livery = self.miz_model.data(idx[2])
            yield Roster.Pilot(pilot_name, aircraft, livery)

    def _transfer_right(self):
        return
        # self.roster_model.beginResetModel()
        # for pilot in self.selected_left:
        #     self.roster.add_pilot_object(pilot)
        # self.roster_model.endResetModel()

    @property
    def miz(self) -> Mission:
        return self._miz

    def _parse_miz_data(self):

        parking_spots.clear_farps()
        for farp in self.miz.farps():
            parking_spots.add_farp(farp)

        miz_data = {}

        for group in self.miz.get_clients_groups():
            assert isinstance(group, Group)
            unit = group.first_unit
            assert isinstance(unit, FlyingUnit)
            try:
                livery = unit.livery
            except KeyError:
                msg = 'no livery found for unit with id "{}" ("{}"), falling back to default'
                logger.error(msg.format(unit.unit_id, unit.unit_type))
                livery = '--default-- (no skin found for this A/C type)'

            pilot_name = group.group_name
            aircraft = unit.unit_type

            line = [group.group_name, unit.unit_type, livery]

            # start_pos = group.group_start_position
            # # print(group.first_unit().unit_position)
            # if start_pos == 'From Parking Area':
            #     start_pos = parking_spots.unit_pos_to_spot(group.first_unit().unit_position)
            #
            #     if start_pos:
            #         line.append('{start_pos.airport}: {start_pos.spot}'.format(start_pos=start_pos))
            #     else:
            #         raise Exception(group.group_id)
            # else:
            #     line.append(start_pos)

            miz_data[pilot_name] = Roster.Pilot(pilot_name, aircraft, livery)

        if len(miz_data) == 0:
            logger.error('no client group found in: {}'.format(self._miz_path.abspath()))
            self.main_ui.error('No client group found in this MIZ file.')

        return miz_data

    def _parse_roster_data(self):

        roster_data = {}

        for pilot in self.roster:
            roster_data[pilot.name] = pilot

        return roster_data

    def tab_roster_show_data_in_table(self, *_):

        miz_data = self._parse_miz_data()
        roster_data = self._parse_roster_data()

        roster_data['Dummy'] = Roster.Pilot('Dummy', 'Dummy', 'Dummy')

        miz_keys = set(k for k in miz_data.keys())
        miz_bg = {k: None for k in miz_keys}
        miz_fg = dict(miz_bg)
        roster_keys = set(k for k in roster_data.keys())
        roster_bg = {k: None for k in roster_keys}
        roster_fg = dict(roster_bg)

        miz_orphans, roster_orphans = miz_keys - roster_keys, roster_keys - miz_keys

        for orphan in miz_orphans:
            roster_data[orphan] = miz_data[orphan]
            roster_fg[orphan] = 'gray'
            roster_bg[orphan] = miz_bg[orphan] = (255, 255, 0, 20)
        for orphan in roster_orphans:
            miz_data[orphan] = roster_data[orphan]
            miz_fg[orphan] = 'gray'
            roster_bg[orphan] = miz_bg[orphan] = (255, 0, 0, 20)

        print(sorted(miz_data.keys()))
        miz_data = list(miz_data[k] for k in sorted(miz_data.keys()))
        roster_data = list(roster_data[k] for k in sorted(roster_data.keys()))
        miz_bg = list(miz_bg[k] for k in sorted(miz_bg.keys()))
        miz_fg = list(miz_fg[k] for k in sorted(miz_fg.keys()))
        roster_bg = list(roster_bg[k] for k in sorted(roster_bg.keys()))
        roster_fg = list(roster_fg[k] for k in sorted(roster_fg.keys()))

        self.miz_model.reset_data(miz_data, miz_bg, fg=miz_fg)
        self.roster_model.reset_data(roster_data, roster_bg, fg=roster_fg)
        self.roster_table.resizeColumnsToContents()
        self.miz_table.resizeColumnsToContents()

    def _load_miz(self):

        miz = BrowseDialog.get_existing_file(
            self,
            'Select MIZ file',
            filter_=['*.miz'],
            init_dir=self._miz_last_dir or saved_games_path.abspath())

        if not miz:
            return

        self._miz_path = miz

        self._miz_last_dir = str(miz.dirname())
        Config().roster_miz_last_dir = self._miz_last_dir
        self.miz_label.setText(miz.abspath())

        def decode_miz():
            with Miz(miz.abspath()) as m:
                self._miz = m.mission

        self.pool.queue_task(
            task=decode_miz,
            _task_callback=I.tab_roster_show_data_in_table
        )

    def _save_miz(self):
        raise NotImplementedError()

    def _save_roster(self):

        roster = BrowseDialog.save_file(
            self,
            'Select roster file',
            filter_=['*.roster'],
            init_dir=self._roster_last_dir or saved_games_path.abspath())

        print(roster)

    def _load_roster(self):

        roster = BrowseDialog.get_existing_file(
            self,
            'Select roster file',
            _filter=['*.roster'],
            init_dir=self._roster_last_dir or saved_games_path.abspath())
