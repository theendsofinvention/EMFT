# coding=utf-8
from itertools import izip, imap
missing = object()

class Odict(dict):
    """Ordered dict implementation.

    :see: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/107747
    """
    def __init__(self, data=None):
        # noinspection PyTypeChecker - ODict interfaces Dict no problemo
        dict.__init__(self, data or {})
        self._keys = dict.keys(self)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        if key not in self._keys:
            self._keys.append(key)

    def __iter__(self):
        return iter(self._keys)
    iterkeys = __iter__

    def clear(self):
        dict.clear(self)
        self._keys = []

    def copy(self):
        d = Odict()
        d.update(self)
        return d

    def items(self):
        return zip(self._keys, self.values())

    def iteritems(self):
        return zip(self._keys, self.itervalues())

    def keys(self):
        return self._keys[:]

    def pop(self, key, default=missing):
        if default is missing:
            return dict.pop(self, key)
        elif key not in self:
            return default
        self._keys.remove(key)
        return dict.pop(self, key, default)

    def popitem(self, key):
        self._keys.remove(key)
        return dict.popitem(key)

    def setdefault(self, key, failobj = None):
        dict.setdefault(self, key, failobj)
        if key not in self._keys:
            self._keys.append(key)

    def update(self, d):
        for (key, val) in d.items():
            self[key] = val

    def values(self):
        return map(self.get, self._keys)

    def itervalues(self):
        return imap(self.get, self._keys)