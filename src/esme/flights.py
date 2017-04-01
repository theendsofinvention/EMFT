# coding=utf-8
"""
Nope
"""
from src.miz.mission import Group
from utils.custom_logging import make_logger, Logged

LOGGER = make_logger('flights')


class Flights(Logged):

    def __init__(self):
        super().__init__()
        self.d = {}

    def add_flight(self, flight):
        if not isinstance(flight, Flight):
            raise Exception('TODO')
        if flight.id in self.d.keys():
            raise Exception('TODO')
        self.d[flight.id] = flight

    def remove_flight(self, flight):
        if not isinstance(flight, Flight):
            raise Exception('TODO')
        if flight.id not in self.d.keys():
            raise Exception('TODO')
        del self.d[flight.id]

    def populate_from_miz(self, miz):
        print(miz.mission)
        for group in miz.mission.groups:
            if group.group_is_client_group:
                flight = Flight(group)
                self.add_flight(flight)

    @property
    def flights(self):
        for _, flight in self.d.items():
            yield flight


class Flight(Logged):

    def __init__(self, group):
        super().__init__()
        assert isinstance(group, Group)
        self.group = group
        if not self.group.group_is_client_group:
            raise Exception('Not a "Client" group')

    @property
    def id(self):
        return self.group.group_id

    @property
    def name(self):
        return self.group.group_name
