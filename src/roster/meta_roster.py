# coding=utf-8

from src.meta import Meta
from utils import Path


class MetaRoster(Meta):

    @property
    def meta_version(self):
        return 1

    @property
    def meta_header(self):
        return 'ROSTER'

    def meta_version_upgrade(self, from_version):
        return True

    def __init__(self, path):
        path = Path(path)
        Meta.__init__(self, path)
