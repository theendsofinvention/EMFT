# coding=utf-8

from .base_gh_object import BaseGHObject, json_property


class GHUser(BaseGHObject):
    @json_property
    def login(self):
        """"""

    @json_property
    def html_url(self):
        """"""

    @json_property
    def url(self):
        """"""

    @json_property
    def id(self):
        """"""

    @json_property
    def avatar_url(self):
        """"""

    @json_property
    def repos_url(self):
        """"""

    @json_property
    def type(self):
        """"""

    @json_property
    def company(self):
        """"""

    @json_property
    def blog(self):
        """"""

    @json_property
    def location(self):
        """"""

    @json_property
    def bio(self):
        """"""

    @json_property
    def public_repos(self):
        """"""

    @json_property
    def public_gists(self):
        """"""

    @json_property
    def created_at(self):
        """"""

    @json_property
    def updated_at(self):
        """"""

    @json_property
    def email(self):
        """"""
