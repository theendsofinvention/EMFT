# coding=utf-8

from src.meta import MetaFile
from src.utils import Path


class MetaFileRoster(MetaFile):

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
        MetaFile.__init__(self, path)
