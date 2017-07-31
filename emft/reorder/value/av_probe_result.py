# coding=utf-8
import humanize


class AVProbeResult:
    __slots__ = [
        '_version',
        '_branch',
        '_download_url',
        '_remote_file_name',
        '_remote_file_size',
        '_human_file_size',
    ]

    def __init__(
            self,
            version: str,
            branch: str,
            download_url: str,
            remote_file_size: int,
            remote_file_name: str,
    ):
        self._version = version
        self._branch = branch
        self._download_url = download_url
        self._remote_file_size = remote_file_size
        self._remote_file_name = remote_file_name
        self._human_file_size = humanize.naturalsize(remote_file_size)

    @property
    def version(self):
        return self._version

    @property
    def branch(self):
        return self._branch

    @property
    def download_url(self):
        return self._download_url

    @property
    def remote_file_size(self):
        return self._remote_file_size

    @property
    def remote_file_name(self):
        return self._remote_file_name

    @property
    def human_file_size(self):
        return self._human_file_size
