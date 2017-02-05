# coding=utf-8

from .base_gh_object import BaseGHObject, json_property


class GHObject(BaseGHObject):
    @json_property
    def type(self):
        """"""

    @json_property
    def sha(self):
        """"""

    @json_property
    def url(self):
        """"""
