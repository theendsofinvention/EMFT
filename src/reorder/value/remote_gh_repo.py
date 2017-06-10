import typing

from src.misc.github import GHProbe, Branch


class RemoteGHRepo:
    def __init__(self, repo_owner: str, repo_name: str):
        self._repo_owner = repo_owner
        self._repo_name = repo_name
        self._probe = GHProbe(repo_owner, repo_name)

    @property
    def repo_owner(self) -> str:
        return self._repo_owner

    @property
    def repo_name(self) -> str:
        return self._repo_name

    def refresh_remote_branches(self):
        self._probe.get_available_branches()

    @property
    def branches(self) -> typing.Iterator[Branch]:
        for branch in self._probe.branches:
            yield branch

    @property
    def branches_as_str(self) -> typing.Iterator[str]:
        for branch in self._probe.branches:
            yield branch.name
