# coding=utf-8

from .base_gh_object import BaseGHObject, json_property


class GHMail(BaseGHObject):
    @json_property
    def email(self):
        """"""

    @json_property
    def verified(self):
        """"""

    @json_property
    def primary(self):
        """"""


class GHMailList(BaseGHObject):
    def __iter__(self):
        for x in self.json:
            yield GHMail(x)

    def __getitem__(self, item) -> GHMail:
        for mail in self:
            if mail.email == item:
                return mail
        raise AttributeError('email address not found: {}'.format(item))

    def __contains__(self, item) -> bool:
        try:
            self.__getitem__(item)
            return True
        except AttributeError:
            return False

    def __len__(self) -> int:
        return len(self.json)
