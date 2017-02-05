# coding=utf-8

import abc


class ISentryContextProvider(metaclass=abc.ABCMeta):
    """
    Interface for any object that would like to register context with Sentry.

    Needs to be implemented, otherwise the crash_reporter will whine about it and crash.
    """

    @abc.abstractmethod
    def get_context(self) -> dict:
        """Returns some context for Sentry"""
