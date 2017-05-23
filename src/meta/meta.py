# coding=utf-8
from .abstract import AbstractMeta
from collections import OrderedDict
from ruamel.yaml import dump as ydump, load as yload, RoundTripDumper


class Meta(AbstractMeta):
    ignore_keys = [
        'meta_version',
    ]

    def __init__(self, init_dict: OrderedDict):

        if init_dict is None:
            self._data = OrderedDict()

        else:

            if not isinstance(init_dict, OrderedDict):
                raise TypeError('expected a OrderedDict, got "{}"'.format(type(init_dict)))

            self._data = init_dict

        self._values, self._keys, self._items = None, None, None
        self._init_views()

    # noinspection PyArgumentList
    def _init_views(self):
        self._values = self._data.values()
        self._keys = self._data.keys()
        self._items = self._data.items()

    def get_context(self):
        return self.data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value: OrderedDict):

        if not isinstance(value, OrderedDict):
            raise TypeError('expected a OrderedDict, got "{}"'.format(type(value)))

        self._data = value
        self._init_views()

    def __len__(self):
        # noinspection PyTypeChecker
        return len(self.data)

    def __iter__(self):
        for k in self.keys():
            if k not in Meta.ignore_keys:
                yield k

    def __contains__(self, x):
        # noinspection PyArgumentList
        return self._data.__contains__(x)

    def __delitem__(self, key, _write=False):
        del self.data[key]

        if _write:
            self.write()

    def __setitem__(self, key, value, _write=False):
        self.data[key] = value

        if _write:
            self.write()

    def __getitem__(self, key):
        return self._data.get(key, None)

    def __str__(self):
        # noinspection PyArgumentList
        return self.data.__str__()

    def __repr__(self):
        return '{}: {}'.format(self.__class__.__name__, self.data.__repr__())

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def items(self):
        return self._items

    def dump(self):
        return ydump(self.data, Dumper=RoundTripDumper, default_flow_style=False)

    def load(self, data):
        self.data = yload(data)