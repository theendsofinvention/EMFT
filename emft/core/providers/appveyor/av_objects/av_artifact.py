# coding=utf-8

import urllib.parse

from emft.core.providers.json_object import JSONObject, json_property


# flake8: noqa
class AVArtifact(JSONObject):
    @json_property
    def type(self):
        """"""

    # noinspection PyPep8Naming
    @json_property
    def fileName(self) -> str:
        """"""

    @json_property
    def name(self) -> str:
        """"""

    @json_property
    def size(self) -> int:
        """"""

    @property
    def url_safe_file_name(self):
        return urllib.parse.quote(self.fileName, safe='')


class AllAVArtifacts(JSONObject):
    def __iter__(self):
        for x in self.json:
            yield AVArtifact(x)

    def __len__(self) -> int:
        return len(self.json)

    def __getitem__(self, item) -> AVArtifact:
        if isinstance(item, int):
            if item > self.__len__():
                raise IndexError(item)
            return AVArtifact(self.json[item])

        elif isinstance(item, str):
            for asset in self:
                if asset.name == item:
                    return asset
            else:
                raise ValueError('no artifact found with name: {}'.format(item))

        raise NotImplementedError('__getitem__ not implemented for type: {}'.format(type(item)))

    def __contains__(self, item: str) -> bool:
        try:
            self.__getitem__(item)
            return True
        except AttributeError:
            return False
