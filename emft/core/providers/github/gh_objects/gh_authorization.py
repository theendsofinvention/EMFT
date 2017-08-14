# coding=utf-8

from emft.core.providers.json_object import JSONObject, json_property
from .gh_app import GHApp


class GHAuthorization(JSONObject):
    @json_property
    def id(self):
        """"""

    @json_property
    def url(self):
        """"""

    @json_property
    def scopes(self):
        """"""

    @json_property
    def token(self):
        """"""

    @json_property
    def token_last_eight(self):
        """"""

    @json_property
    def hashed_token(self):
        """"""

    def app(self) -> GHApp:
        return GHApp(self.json['app'])

    @json_property
    def note(self):
        """"""

    @json_property
    def note_url(self):
        """"""

    @json_property
    def updated_at(self):
        """"""

    @json_property
    def created_at(self):
        """"""

    @json_property
    def fingerprint(self):
        """"""
