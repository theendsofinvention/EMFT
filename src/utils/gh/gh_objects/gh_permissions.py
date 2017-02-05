# coding=utf-8

from .base_gh_object import BaseGHObject, json_property


class GHPermissions(BaseGHObject):
    @json_property
    def admin(self):
        """"""

    @json_property
    def push(self):
        """"""

    @json_property
    def pull(self):
        """"""
