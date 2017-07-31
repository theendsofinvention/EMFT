# coding=utf-8

from emft.utils.custom_session import JSONObject, json_property
from .gh_object import GHObject


class GHRef(JSONObject):
    @json_property
    def ref(self):
        """"""

    @json_property
    def url(self):
        """"""

    def object(self):
        return GHObject(self.json['object'])
