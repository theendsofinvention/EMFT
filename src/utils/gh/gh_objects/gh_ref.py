# coding=utf-8

from .base_gh_object import BaseGHObject, json_property
from .gh_object import GHObject


class GHRef(BaseGHObject):
    @json_property
    def ref(self):
        """"""

    @json_property
    def url(self):
        """"""

    def object(self):
        return GHObject(self.json['object'])
