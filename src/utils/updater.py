# coding=utf-8
import semver

# noinspection PyProtectedMember
from src import _global
import humanize
from .progress import Progress
from .downloader import Downloader
from src.ui.main_ui_interface import I
import io
import os
import subprocess
from .threadpool import ThreadPool

# noinspection PyPep8Naming
from src.utils.gh import GHRelease, GHSession as GH

from src.utils.custom_logging import make_logger

gh = GH()

logger = make_logger(__name__)


class _Release:
    def __init__(self, gh_release: GHRelease):
        self._gh_release = gh_release
        self._channel = None

    @property
    def version(self):
        return self._gh_release.version

    @property
    def assets(self):
        return self._gh_release.assets()

    @property
    def channel(self) -> str or None:
        if self._channel is None:
            v = semver.parse_version_info(self._gh_release.version)
            if v.prerelease is None:
                self._channel = 'stable'
            elif v.prerelease.startswith('a.'):
                self._channel = 'alpha'
            elif v.prerelease.startswith('b.'):
                self._channel = 'beta'
            elif v.prerelease.startswith('dev'):
                self._channel = 'dev'
            elif v.prerelease.startswith('dev'):
                self._channel = 'dev'

        return self._channel


class Updater:
    def __init__(
            self,
            current: str,
            gh_user: str,
            gh_repo: str,
            asset_filename: str,
            pre_update_func: callable = None,
            cancel_update_func: callable = None,
    ):

        self._latest = None
        self._current = current
        self._gh_user = gh_user
        self._gh_repo = gh_repo
        self._available = {}
        self._candidates = {}
        self._latest_release = None
        self._asset_filename = asset_filename
        self._pre_update = pre_update_func
        self._cancel_update_func = cancel_update_func

        self._update_ready_to_install = False

        self.pool = ThreadPool(_num_threads=1, _basename='updater', _daemon=True)

    def _get_available_releases(self):

        logger.debug('querying GH API for available releases')
        releases = gh.get_all_releases(self._gh_user, self._gh_repo)

        if releases:
            for rel in releases:
                logger.debug('release found: {}'.format(rel.version))
                self._available[rel.version] = _Release(rel)

    @property
    def available(self) -> list or None:
        return self._available

    @property
    def latest(self) -> _Release or None:
        return self._latest

    def _version_check(self):

        logger.info('checking for new version')

        self._get_available_releases()

        for version, release in self._available.items():
            assert isinstance(release, _Release)

            logger.debug('comparing current with remote: "{}" vs "{}"'.format(self._current, version))

            if semver.compare(version, self._current) > 0:
                logger.debug('this version is newer: {}'.format(version))
                self._candidates[version] = release

    def _process_candidates(self):

        if self._candidates:

            if self._pre_update is not None:
                self._pre_update()

            latest = self._current

            for version, release in self._candidates.items():
                logger.debug('comparing "{}" and "{}"'.format(latest, version))

                if semver.compare(version, latest) > 0:
                    logger.debug('{} is newer'.format(version))
                    latest = version
                    self._latest_release = release

        else:
            if self._cancel_update_func:
                self._cancel_update_func()

    @staticmethod
    def _progress_hook(data):
            label = 'Time left: {} ({}/{})'.format(
                data['time'],
                humanize.naturalsize(data['downloaded']),
                humanize.naturalsize(data['total'])
            )
            Progress.set_label(label)
            Progress.set_value(data['downloaded'] / data['total'] * 100)

    def _download_latest_release(self):

        if self._latest_release:

            logger.debug('downloading latest release asset')

            assert isinstance(self._latest_release, _Release)
            assets = self._latest_release.assets

            for asset in assets:
                if asset.name == self._asset_filename:
                    Progress.start('Downloading latest version', 100, '')
                    d = Downloader(
                        url=asset.browser_download_url,
                        filename='./update',
                        progress_hooks=[self._progress_hook],
                    )
                    if d.download():
                        self._update_ready_to_install = True

        else:
            if self._cancel_update_func:
                self._cancel_update_func()

    def _install_update(self):

        if self._update_ready_to_install:
            logger.debug('installing update')
            # noinspection SpellCheckingInspection
            bat_liiiiiiiiiiiines = [  # I'm deeply sorry ...
                '@echo off',
                'echo Updating to latest version...',
                'ping 127.0.0.1 - n 5 - w 1000 > NUL',
                'move /Y "update" "{}.exe" > NUL'.format(_global.APP_SHORT_NAME),
                'echo restarting...',
                'start "" "{}.exe"'.format(_global.APP_SHORT_NAME),
                'DEL update.vbs',
                'DEL "%~f0"',
            ]
            with io.open('update.bat', 'w', encoding='utf-8') as bat:
                bat.write('\n'.join(bat_liiiiiiiiiiiines))

            with io.open('update.vbs', 'w', encoding='utf-8') as vbs:
                # http://www.howtogeek.com/131597/can-i-run-a-windows-batch-file-without-a-visible-command-prompt/
                vbs.write('CreateObject("Wscript.Shell").Run """" '
                          '& WScript.Arguments(0) & """", 0, False')
            logger.debug('starting update batch file')
            args = ['wscript.exe', 'update.vbs', 'update.bat']
            subprocess.Popen(args)
            # noinspection PyProtectedMember
            os._exit(0)

        else:
            if self._cancel_update_func:
                self._cancel_update_func()

    def version_check(self):

        self.pool.queue_task(self._version_check, _err_callback=self._cancel_update_func)

        self.pool.queue_task(self._process_candidates, _err_callback=self._cancel_update_func)

        self.pool.queue_task(self._download_latest_release, _err_callback=self._cancel_update_func)

        self.pool.queue_task(self._install_update, _err_callback=self._cancel_update_func)
