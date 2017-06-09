from src.meta import MetaFile, MetaProperty, MetaGUIDProperty
from src.utils import Path, make_logger
from collections.abc import Set

logger = make_logger(__name__)


class ReorderProfile(MetaFile):
    def meta_version_upgrade(self, from_version):
        return True

    @property
    def meta_version(self):
        return 1

    @property
    def meta_header(self):
        return 'REORDER_PROFILE'

    def __init__(self, profile_name: str):
        MetaFile.__init__(self, path=f'./{profile_name}.profile')
        if self.path.exists():
            self.read()
        self._name = profile_name

    @MetaProperty(str)
    def gh_owner(self, value: str) -> str:
        return value

    @MetaProperty(str)
    def gh_repo(self, value: str) -> str:
        return value

    @MetaProperty(str)
    def av_owner(self, value: str) -> str:
        return value

    @MetaProperty(str)
    def av_repo(self, value: str) -> str:
        return value

    @MetaGUIDProperty(str)
    def src_folder(self, value: str) -> str:
        return value

    @MetaGUIDProperty(str)
    def output_folder(self, value: str) -> str:
        return value
