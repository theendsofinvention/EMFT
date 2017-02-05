# coding=utf-8

from .base_gh_object import BaseGHObject, json_property
from .gh_permissions import GHPermissions
from .gh_user import GHUser


class GHRepo(BaseGHObject):
    def owner(self) -> GHUser:
        return GHUser(self.json['owner'])

    def permissions(self):
        return GHPermissions(self.json['permissions'])

    def source(self):
        if 'source' in self.json.keys():
            return GHRepo(self.json['source'])

    @json_property
    def id(self):
        """"""

    @json_property
    def name(self):
        """"""

    @json_property
    def full_name(self):
        """"""

    @json_property
    def description(self):
        """"""

    @json_property
    def private(self):
        """"""

    @json_property
    def fork(self):
        """"""

    @json_property
    def url(self):
        """"""

    @json_property
    def html_url(self):
        """"""

    @json_property
    def archive_url(self):
        """"""

    @json_property
    def branches_url(self):
        """"""

    @json_property
    def clone_url(self):
        """"""

    @json_property
    def commits_url(self):
        """"""

    @json_property
    def downloads_url(self):
        """"""

    @json_property
    def size(self):
        """"""

    @json_property
    def default_branch(self):
        """"""

    @json_property
    def open_issues_count(self):
        """"""

    @json_property
    def pushed_at(self):
        """"""

    @json_property
    def created_at(self):
        """"""

    @json_property
    def updated_at(self):
        """"""

    @json_property
    def subscribers_count(self):
        """"""

    @json_property
    def tags_url(self):
        """"""


class GHRepoList(BaseGHObject):
    def __iter__(self):
        for x in self.json:
            yield GHRepo(x)

    def __getitem__(self, item) -> GHRepo:
        for repo in self:
            if repo.name == item:
                return repo
        raise AttributeError('repository not found: {}'.format(item))

    def __contains__(self, item) -> bool:
        try:
            self.__getitem__(item)
            return True
        except AttributeError:
            return False

    def __len__(self) -> int:
        return len(self.json)
