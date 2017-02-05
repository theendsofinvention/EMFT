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
