# coding=utf-8


# noinspection PyPep8Naming
class json_property:  # noqa: N801
    """Wraps around properties to extract JSON key"""

    def __init__(self, func):
        self.key = func.__name__
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj, _):
        if obj is None:  # pragma: no cover
            return self
        if not hasattr(obj, 'json'):
            raise NotImplementedError('this object does not support JSON properties')
        return obj.json.get(self.key, None)


class JSONObject:
    def __init__(self, json: dict):
        self._json = json

    @property
    def json(self) -> dict:
        return self._json

    def get_all(self):  # pragma: no cover
        ret = set()
        for k in self.__class__.__dict__:
            if k.startswith('__'):
                continue
            if callable(getattr(self, k)):
                ret.add((k, getattr(self, k)().get_all()))
            else:
                ret.add((k, getattr(self, k)))
        return ret

    def print_all(self, indent=''):
        for k in sorted((k for k in self.__class__.__dict__)):
            if k.startswith('__'):
                continue
            else:
                a = getattr(self, k)
                if callable(a):
                    print(indent, k, 'count:', len(list(a())))
                elif hasattr(a, 'print_all'):
                    print(indent, k, ':')
                    getattr(a, 'print_all')(indent + '  ')
                else:
                    print(indent, k, ':', a)
