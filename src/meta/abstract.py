# coding=utf-8
import abc

from src.sentry.sentry_context_provider import ISentryContextProvider


class AbstractMeta(ISentryContextProvider, metaclass=abc.ABCMeta):
    """
    Defines the interface for a class that holds Metadata.
    """

    @abc.abstractmethod
    def dump(self):
        """pass"""

    @abc.abstractmethod
    def load(self, data):
        """pass"""


class AbstractMetaFile(AbstractMeta, metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def meta_header(self):
        """"""

    @property
    @abc.abstractmethod
    def meta_version(self):
        """"""

    @abc.abstractmethod
    def meta_version_upgrade(self, from_version):
        """"""

    @abc.abstractmethod
    def read(self):
        """Reads meta from file"""

    @abc.abstractmethod
    def write(self):
        """Writes meta to file"""

    @abc.abstractmethod
    def __getitem__(self, item):
        """Returns an item's value"""

    @abc.abstractmethod
    def __setitem__(self, item, value):
        """Sets an item's value"""