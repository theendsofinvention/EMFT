# coding=utf-8

import re
import urllib.parse


class AVVersion:
    VERSION_RE = re.compile(
        r'^'
        r'(?P<version_str>[^+]+)'
        r'\+'
        r'('
        r'(?P<metadata>[0-9]+)'
        r'\.'
        r')?'
        r'Branch'
        r'\.'
        r'(?P<branch>.+)'
        r'\.'
        r'Sha'
        r'\.'
        r'(?P<sha>[a-f0-9]+)'
        r'\.'
        r'(?P<av_build>[0-9]+)'
        r'$')

    def __init__(self, version_str):
        self._full_version_str = version_str

    @property
    def _version(self):
        if not hasattr(self, '_parsed_version'):
            parsed_version = self.VERSION_RE.match(self._full_version_str)
            if not parsed_version:
                raise ValueError('failed to parse version str: {}'.format(self._full_version_str))
            setattr(self, '_parsed_version', parsed_version)
        return getattr(self, '_parsed_version')

    @property
    def url_safe_version_str(self):
        return urllib.parse.quote(self._full_version_str, safe='')

    @property
    def version_str(self):
        return self._version.group('version_str')

    @property
    def branch(self):
        return self._version.group('branch')

    @property
    def sha(self):
        return self._version.group('sha')

    @property
    def av_build(self):
        return self._version.group('av_build')

    def print_all(self, indent=''):
        for x in ['version_str', 'branch', 'sha', 'av_build']:
            print(indent, x, ':', getattr(self, x))
