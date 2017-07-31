# coding=utf-8

from src.utils.custom_session import JSONObject, json_property
from .av_nu_get_feed import AVNuGetFeed


# flake8: noqa
# noinspection PyPep8Naming
class AVProject(JSONObject):
    @json_property
    def projectId(self):
        """"""

    @json_property
    def accountId(self):
        """"""

    @json_property
    def accountName(self):
        """"""

    @json_property
    def builds(self):
        """"""

    @json_property
    def name(self):
        """"""

    @json_property
    def slug(self):
        """"""

    @json_property
    def repositoryType(self):
        """"""

    @json_property
    def repositoryScm(self):
        """"""

    @json_property
    def repositoryName(self):
        """"""

    @json_property
    def repositoryBranch(self):
        """"""

    @json_property
    def isPrivate(self):
        """"""

    @json_property
    def skipBranchesWithoutAppveyorYml(self):
        """"""

    @property
    def nuGetFeed(self):
        return AVNuGetFeed(self.json['nuGetFeed'])

    @json_property
    def created(self):
        """"""

    @json_property
    def updated(self):
        """"""
