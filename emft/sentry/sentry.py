# coding=utf-8

import logging
import sys

import certifi
import raven
import raven.breadcrumbs
import raven.conf
import raven.handlers.logging

from emft import global_
from emft.__version__ import __version__
from emft.sentry.sentry_context_provider import ISentryContextProvider
from emft.utils import Singleton, make_logger

LOGGER = make_logger(__name__)

CRASH = False


class Sentry(raven.Client, metaclass=Singleton):
    def __init__(self):
        self.registered_contexts = {}
        raven.Client.__init__(
            self,
            'https://da606739b60743859ffc04963d6ea1a3:'
            '59825849c3884a52a0244e7f1c30260b@sentry.io/135324?ca_certs={}'.format(certifi.where()),
            release=__version__
        )
        LOGGER.info('Sentry is ready')

    def set_context(self):
        self.tags_context(
            dict(
                frozen=global_.FROZEN,
                platform=sys.platform,
                release_name=global_.APP_RELEASE_NAME,
            )
        )
        try:
            self.tags_context(dict(windows_version=sys.getwindowsversion()))
        except AttributeError:
            pass

    def register_context(self, context_name: str, context_provider: ISentryContextProvider):
        """Registers a context to be read when a crash occurs; obj must implement get_context()"""
        LOGGER.debug('registering context with Sentry: {}'.format(context_name))
        self.registered_contexts[context_name] = context_provider

    @staticmethod
    def add_crumb(message, category, level):
        raven.breadcrumbs.record(message=message, category=category, level=level)

    def captureMessage(self, message, **kwargs):  # noqa: N802
        self.set_context()
        if not global_.FROZEN:
            LOGGER.warning(f'message would have been sent: {message}')
            return
        if kwargs.get('data') is None:
            kwargs['data'] = {}
        if kwargs['data'].get('level') is None:
            kwargs['data']['level'] = logging.DEBUG
        for context_name, context_provider in self.registered_contexts.items():
            assert isinstance(context_provider, ISentryContextProvider)
            SENTRY.extra_context({context_name: context_provider.get_context()})
        super(Sentry, self).captureMessage(message, **kwargs)

    def captureException(self, exc_info=None, **kwargs):  # noqa: N802
        self.set_context()
        if not global_.FROZEN:
            LOGGER.error('crash report would have been sent')
            return

        LOGGER.debug('capturing exception')
        for k, context_provider in self.registered_contexts.items():
            assert isinstance(context_provider, ISentryContextProvider)
            SENTRY.extra_context({k: context_provider.get_context()})
        super(Sentry, self).captureException(exc_info, **kwargs)

        if CRASH:
            raise DeprecationWarning('this had been deprecated')


LOGGER.info('SENTRY: initializing')
SENTRY = Sentry()
LOGGER.info('SENTRY: initialized')


# noinspection PyUnusedLocal
def filter_breadcrumbs(_logger, level, msg, *args, **kwargs):
    skip_lvl = []
    skip_msg = []

    if level in skip_lvl or msg in skip_msg:
        return False

    # print('got args, kwargs: ', args, kwargs)
    if _logger == 'requests':
        return False
    return True


raven.breadcrumbs.register_special_log_handler('__main__', filter_breadcrumbs)
