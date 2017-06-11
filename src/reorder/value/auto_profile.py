# coding=utf-8
import typing
from collections import MutableMapping

from src.utils import make_logger, Singleton

logger = make_logger(__name__)


# noinspection PyAbstractClass
class AutoProfile:
    __slots__ = ['name', 'gh_repo', 'av_repo', 'src_folder', 'output_folder']

    def __init__(
            self,
            name: str,
            gh_repo: str,
            av_repo: str,
            src_folder: str,
            output_folder: str,
    ):
        self.name = name
        self.gh_repo = gh_repo
        self.av_repo = av_repo
        self.src_folder = src_folder
        self.output_folder = output_folder


class AutoProfiles(MutableMapping, metaclass=Singleton):
    ACTIVE_PROFILE = None

    def __init__(self, init_dict: dict = None):
        self._data = init_dict or dict()

    def __getitem__(self, key) -> AutoProfile:
        return self._data.__getitem__(key)

    def __iter__(self) -> typing.Iterator[str]:
        return self._data.__iter__()

    def values(self) -> typing.List[AutoProfile]:
        return list(self._data.values())

    def items(self) -> typing.List[typing.Tuple[str, AutoProfile]]:
        return list(self._data.items())

    @property
    def data(self) -> dict:
        return self._data

    def __len__(self) -> int:
        return self._data.__len__()

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __setitem__(self, key, value: AutoProfile):
        return self._data.__setitem__(key, value)
