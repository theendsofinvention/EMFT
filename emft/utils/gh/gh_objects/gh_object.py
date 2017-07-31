# coding=utf-8

from emft.utils.custom_session import JSONObject, json_property


class GHObject(JSONObject):
    @json_property
    def type(self):
        """"""

    @json_property
    def sha(self):
        """"""

    @json_property
    def url(self):
        """"""
