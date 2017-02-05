# coding=utf-8

from .base_gh_object import BaseGHObject, json_property


class GHApp(BaseGHObject):
    @json_property
    def url(self):
        """"""

    @json_property
    def name(self):
        """"""

    @json_property
    def client_id(self):
        """"""
