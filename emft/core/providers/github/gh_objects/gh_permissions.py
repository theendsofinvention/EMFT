# coding=utf-8

from emft.core.providers.json_object import JSONObject, json_property


class GHPermissions(JSONObject):
    @json_property
    def admin(self):
        """"""

    @json_property
    def push(self):
        """"""

    @json_property
    def pull(self):
        """"""
