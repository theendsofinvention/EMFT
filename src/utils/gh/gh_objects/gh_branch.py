# coding=utf-8

from src.utils.custom_session import JSONObject, json_property
from .gh_commit import GHCommit


class GHBranch(JSONObject):
    @json_property
    def name(self):
        """"""

    @property
    def html_url(self) -> GHCommit:
        return GHCommit(self.json['commit'])


class GHAllBranches(JSONObject):
    def __iter__(self):
        for x in self.json:
            yield GHBranch(x)

    def __getitem__(self, branch_name) -> GHBranch:
        for rel in self:
            if rel.name == branch_name:
                return rel
        raise AttributeError('release not found: {}'.format(branch_name))

    def __len__(self) -> int:
        return len(self.json)

    def __contains__(self, branch_name) -> bool:
        try:
            self.__getitem__(branch_name)
            return True
        except AttributeError:
            return False
