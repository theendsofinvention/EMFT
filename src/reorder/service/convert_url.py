# coding=utf-8

import re

from src.sentry import SENTRY
from ..value.remote_av_repo import RemoteAVRepo
from ..value.remote_gh_repo import RemoteGHRepo

_re_av = [
    re.compile(r'https://ci.appveyor.com/project/(?P<repo_owner>[^/]*)/(?P<repo_name>[^/]*)(/.*)?'),
]

_re_gh = [
    re.compile(r'^(https://|git@)github\.com[/:]{1}(?P<repo_owner>[^\./]+)/(?P<repo_name>[^\./]+)(\.git|/.*)?$'),
]


class ConvertUrl:
    @staticmethod
    def __convert(base_class: callable, regex_list: list, url_str: str):
        for regex in regex_list:
            m = regex.match(url_str)
            if m:
                return base_class(m.group('repo_owner'), m.group('repo_name'))
        SENTRY.captureMessage(f'failed to parse url: {url_str}')
        raise ValueError(url_str)

    @staticmethod
    def convert_gh_url(gh_repo_url: str) -> RemoteGHRepo:
        return ConvertUrl.__convert(RemoteGHRepo, _re_gh, gh_repo_url)

    @staticmethod
    def convert_av_url(av_repo_url: str) -> RemoteAVRepo:
        return ConvertUrl.__convert(RemoteAVRepo, _re_av, av_repo_url)
