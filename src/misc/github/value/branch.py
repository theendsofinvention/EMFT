from src.meta import Meta, MetaProperty
from collections.abc import MutableSequence
import typing


class Branch(Meta):

    def __init__(self, brach_name: str):
        Meta.__init__(self)
        self.name = brach_name

    @MetaProperty(str)
    def name(self, value: str) -> str:
        return value


class BranchesArray(MutableSequence, Meta):

    def __init__(self, branches: typing.List['Branch'] = None):
        Meta.__init__(self)
        self.branches = branches or list()

    @MetaProperty(typing.List[Branch])
    def branches(self, value: typing.List['Branch']) -> typing.List[Branch]:
        return value

    def insert(self, index, value):
        self.branches.insert(index, value)

    def __getitem__(self, index):
        self.branches.__getitem__(index)

    def __setitem__(self, key, value):
        self.branches.__setitem__(key, value)

    def __len__(self):
        return len(self.branches)

    def __delitem__(self, index):
        self.branches.__delitem__(index)