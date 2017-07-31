# coding=utf-8

from emft.utils.custom_session import JSONObject, json_property


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
