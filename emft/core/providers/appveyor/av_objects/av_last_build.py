# coding=utf-8

from emft.core.providers.json_object import JSONObject
from .av_build import AVBuild
from .av_project import AVProject


class AVLastBuild(JSONObject):
    @property
    def project(self):
        return AVProject(self.json['project'])

    @property
    def build(self):
        return AVBuild(self.json['build'])
