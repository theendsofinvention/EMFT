# coding=utf-8

import requests

from src.utils.custom_logging import make_logger
from .av_objects.av_artifact import AllAVArtifacts
from .av_objects.av_history import AVHistory
from .av_objects.av_last_build import AVLastBuild

LOGGER = make_logger(__name__)


class AVSession(requests.Session):
    def __init__(self):

        requests.Session.__init__(self)

        self.base = [r'https://ci.appveyor.com/api']

        self.__resp = None

        self.req = None

    @property
    def resp(self) -> requests.models.Response:
        return self.__resp

    def build_req(self, *args):

        if not args:
            raise ValueError('request is empty')

        for x in args:
            if not isinstance(x, str):
                raise TypeError('expected a string, got: {} ({})'.format(x, args))

        self.req = '/'.join(self.base + list(args))

        return self.req

    def __parse_resp_error(self):

        LOGGER.error(self.req)
        LOGGER.error(self.resp)
        LOGGER.error(self.__resp.reason)

        raise Exception('request failed')

    def __parse_resp(self) -> requests.models.Response:

        if self.__resp is None:
            raise Exception('did not get any response from: {}'.format(self.req))

        if not self.__resp.ok:
            self.__parse_resp_error()

        LOGGER.debug(self.__resp.reason)

        return self.__resp

    def _get(self, **kwargs) -> requests.models.Response:

        LOGGER.debug(self.req)

        self.__resp = super(AVSession, self).get(self.req, **kwargs)

        return self.__parse_resp()

    def _get_json(self, **kwargs) -> requests.models.Response:

        req = self._get(**kwargs)

        return req.json()

    def get_last_build(self, av_user_name, av_project_name, branch: str = None) -> AVLastBuild:

        req_params = ['projects', av_user_name, av_project_name]

        if branch:
            req_params.extend(['branch', branch])

        self.build_req(*req_params)

        return AVLastBuild(self._get_json())

    def get_artifacts(self, job_id) -> AllAVArtifacts:

        self.build_req('buildjobs', job_id, 'artifacts')

        return AllAVArtifacts(self._get_json())

    def get_history(self, av_user_name, av_project_name, build_count=9999) -> AVHistory:
        """
        Gets build history from the top down
        :param build_count: max number of builds to retrieve
        :param av_user_name: AV user name
        :param av_project_name: AV project name
        :return: AVHistory object
        """

        self.build_req('projects', av_user_name, av_project_name, 'history?recordsNumber={}'.format(build_count))

        return AVHistory(self._get_json())

    def get_latest_build_on_branch(self, av_user_name, av_project_name, branch) -> AVLastBuild:

        self.build_req('projects', av_user_name, av_project_name, 'branch', branch)

        return AVLastBuild(self._get_json())

    def get_build_by_version(self, av_user_name, av_project_name, build_id) -> AVLastBuild:

        self.build_req('projects', av_user_name, av_project_name, 'build', build_id)

        return AVLastBuild(self._get_json())
