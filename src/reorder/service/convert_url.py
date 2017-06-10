# coding=utf-8
import re
import typing

from src.sentry import SENTRY

_re_av = [
    re.compile(r'https://ci.appveyor.com/project/(?P<repo_owner>[^/]*)/(?P<repo_name>[^/]*)(/.*)?'),
]

_re_gh = [
    re.compile(r'^(https://|git@)github\.com[/:]+(?P<repo_owner>[^./]+)/(?P<repo_name>[^./]+)(\.git|/.*)?$'),
]


class ConvertUrl:
    @staticmethod
    def __convert(regex_list: list, url_str: str):
        for regex in regex_list:
            m = regex.match(url_str)
            if m:
                return m.group('repo_owner'), m.group('repo_name')
        SENTRY.captureMessage(f'failed to parse url: {url_str}')
        raise ValueError(url_str)

    @staticmethod
    def convert_gh_url(gh_repo_url: str) -> typing.Tuple[str, str]:
        return ConvertUrl.__convert(_re_gh, gh_repo_url)

    @staticmethod
    def convert_av_url(av_repo_url: str) -> typing.Tuple[str, str]:
        return ConvertUrl.__convert(_re_av, av_repo_url)
