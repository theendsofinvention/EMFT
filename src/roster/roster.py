# coding=utf-8

import typing
from collections import OrderedDict
from collections.abc import Sequence

from .meta_roster import MetaFileRoster


class Roster(Sequence):
    class Pilot(Sequence):

        idx = {
            0: '_name',
            1: '_ac',
            2: '_livery'
        }

        def __getitem__(self, index):
            return getattr(self, self.idx[index])

        def __len__(self):
            return 3

        def __init__(self, pilot_name: str, aircraft: str, livery: str):
            self._name = pilot_name
            self._ac = aircraft
            self._livery = livery
            self._hash = None

        @property
        def name(self):
            return self._name

        @property
        def aircraft(self):
            return self._ac

        @property
        def livery(self):
            return self._livery

        def to_meta(self) -> OrderedDict:
            return OrderedDict(
                name=self._name,
                aircraft=self._ac,
                livery=self._livery
            )

        @staticmethod
        def from_meta(meta: OrderedDict) -> 'Roster.Pilot':
            return Roster.Pilot(meta['name'], meta['aircraft'], meta['livery'])

        def __hash__(self):
            if self._hash is None:
                self._hash = hash('{0.name}{0.aircraft}{0.livery}'.format(self))
            return self._hash

        def __eq__(self, other):
            return self.__hash__() == other.__hash__()

        def __str__(self):
            return '{} ({} - {})'.format(self._name, self._ac, self._livery)

    def __init__(self):
        self.pilots = list()

    def add_pilot_object(self, pilot: 'Roster.Pilot'):
        if pilot not in self:
            self.pilots.append(pilot)

    def add_pilot_from_values(self, pilot_name, aircraft, livery):
        pilot = Roster.Pilot(pilot_name, aircraft, livery)
        self.add_pilot_object(pilot)

    def pilot_by_name(self, pilot_name):
        for pilot in self:
            if pilot.name == pilot_name:
                return pilot

    def __iter__(self) -> typing.Iterator['Roster.Pilot']:
        return self.pilots.__iter__()

    def __len__(self):
        return self.pilots.__len__()

    def __getitem__(self, index):
        return self.pilots.__getitem__(index)

    def to_file(self, file_path):

        meta = MetaFileRoster(file_path)

        for pilot in self:
            meta[pilot.name] = pilot.to_meta()

        meta.write()

    def from_file(self, file_path):

        meta = MetaFileRoster(file_path)
        meta.read()

        for pilot in meta:
            pilot = Roster.Pilot.from_meta(meta[pilot])
            self.add_pilot_from_values(pilot)
