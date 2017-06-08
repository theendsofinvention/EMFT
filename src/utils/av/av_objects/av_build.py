# coding=utf-8

import typing

from src.utils.custom_session import JSONObject, json_property
from .av_job import AVAllJobs
from .av_version import AVVersion


# noinspection PyPep8Naming
class AVBuild(JSONObject):
    @json_property
    def buildId(self):
        """"""

    @property
    def jobs(self):
        return AVAllJobs(self.json['jobs'])

    @json_property
    def buildNumber(self):
        """"""

    @property
    def version(self):
        return AVVersion(self.json['version'])

    @json_property
    def message(self):
        """"""

    @json_property
    def messageExtended(self):
        """"""

    @json_property
    def branch(self):
        """"""

    @json_property
    def commitId(self):
        """"""

    @json_property
    def authorName(self):
        """"""

    @json_property
    def authorUsername(self):
        """"""

    @json_property
    def committerName(self):
        """"""

    @json_property
    def committerUsername(self):
        """"""

    @json_property
    def committed(self):
        """"""

    @json_property
    def status(self):
        """"""

    @json_property
    def started(self):
        """"""

    @json_property
    def finished(self):
        """"""

    @json_property
    def created(self):
        """"""

    @json_property
    def updated(self):
        """"""

    @property
    def artifact(self):
        return


class AVAllBuilds(JSONObject):
    def __iter__(self):
        for x in self.json:
            yield AVBuild(x)

    def successful_only(self) -> typing.Generator[AVBuild, None, None]:
        for x in self:
            if x.status == 'success':
                yield x

    def __getitem__(self, build_id) -> AVBuild:
        for rel in self:
            if rel.buildId == build_id:
                return rel
        raise AttributeError('job not found: {}'.format(build_id))

    def __len__(self) -> int:
        return len(self.json)

    def __contains__(self, build_id) -> bool:
        try:
            self.__getitem__(build_id)
            return True
        except AttributeError:
            return False

    def print_all(self, indent=''):
        # super(AVAllBuilds, self).print_all()
        for x in self:
            try:
                x.print_all('  ')
            except ValueError:
                pass
