import typing

from collections.abc import MutableMapping


class LocalProfiles(MutableMapping):
    __slots__ = ('_data',)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, key):
        return self._data[key]

    def __init__(self, init_dict: dict = None):
        self._data = init_dict or dict()

    def profiles_names(self) -> typing.List[str]:
        return sorted(self._data.keys())


local_profiles = LocalProfiles()
