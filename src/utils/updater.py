# coding=utf-8

import io
import os
import subprocess
from re import compile

import humanize
import semver

from src import _global
from src.utils.custom_logging import make_logger
from src.utils.gh import GHRelease, GHSession as GH
from .downloader import Downloader
from .progress import Progress
from .threadpool import ThreadPool

gh = GH()

logger = make_logger(__name__)


class _Version:
    re_branch = compile(r'.*\.(?P<branch>.*)\..*')

    def __init__(self, version_str: str):
        try:
            semver.parse(version_str)
        except ValueError:
            raise ValueError(version_str)
        self._version_str = version_str
        self._info = semver.parse_version_info(version_str)
        self._channel = None
        self._branch = None

        self._parse()

    def _parse(self):
        if self._info.prerelease is None:
            self._channel = 'stable'
        elif self._info.prerelease.startswith('alpha.'):
            self._channel = 'alpha'
            self._branch = self.re_branch.match(self._info.prerelease).group('branch')
        elif self._info.prerelease.startswith('beta.'):
            self._channel = 'beta'
            self._branch = self.re_branch.match(self._info.prerelease).group('branch')
        elif self._info.prerelease.startswith('dev.'):
            self._channel = 'dev'
        elif self._info.prerelease.startswith('rc.'):
            self._channel = 'rc'
        else:
            raise ValueError(self._info.prerelease)

    @property
    def branch(self) -> str or None:
        return self._branch

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def version_str(self):
        return self._version_str

    def __gt__(self, other):
        return semver.compare(self.version_str, other.version_str) > 0

    def __lt__(self, other):
        return semver.compare(self.version_str, other.version_str) < 0

    def __eq__(self, other):
        return semver.compare(self.version_str, other.version_str) == 0

    def __str__(self):
        return self._version_str


class _Release:
    def __init__(self, gh_release: GHRelease):
        self._gh_release = gh_release
        self._version = _Version(self._gh_release.version)

    @property
    def version(self):
        return self._version

    @property
    def assets(self):
        return self._gh_release.assets()

    @property
    def channel(self) -> str:
        return self._version.channel

    @property
    def branch(self) -> str or None:
        return self._version.branch


class Updater:
    def __init__(
            self,
            current_version: str,
            gh_user: str,
            gh_repo: str,
            asset_filename: str,
            pre_update_func: callable = None,
            cancel_update_func: callable = None,
    ):

        self._latest = None
        self._current = _Version(current_version)
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

    def _version_check(self, channel: str):

        logger.info('checking for new version')

        self._get_available_releases()

        for version, release in self._available.items():

            skip = []

            if channel == 'alpha':
                pass
            elif channel == 'beta':
                skip.append('alpha')
            elif channel == 'dev':
                skip.append('beta')
            elif channel == 'rc':
                skip.append('dev')
            elif channel == 'stable':
                skip.append('rc')
            else:
                raise ValueError(channel)

            assert isinstance(release, _Release)

            logger.debug('comparing current with remote: "{}" vs "{}"'.format(self._current, version))

            version = _Version(version)

            if version.channel in skip:
                logger.debug('skipping release with channel: {}'.format(version.channel))
                continue

            if version.channel in ['alpha', 'beta']:

                logger.debug('comparing branch name')
                if not self._current.branch == version.branch:
                    logger.debug('skipping branch: {}'.format(version.branch))

            if version > self._current:
                logger.debug('this version is newer: {}'.format(version))
                self._candidates[version.version_str] = release

        if self._candidates:

            logger.debug('new version found, following up')
            return True

        else:

            logger.debug('no new version found')
            return False

    def _process_candidates(self):

        if self._candidates:

            if self._pre_update is not None:
                self._pre_update()

            latest = self._current

            for version, release in self._candidates.items():
                logger.debug('comparing "{}" and "{}"'.format(latest, version))

                version = _Version(version)

                if version > self._current:
                    logger.debug('{} is newer'.format(version))
                    latest = version
                    self._latest_release = release

        else:

            logger.debug('no release candidate')

            if self._cancel_update_func:
                self._cancel_update_func()

    def _download_latest_release(self):

        def _progress_hook(data):
            label = 'Time left: {} ({}/{})'.format(
                data['time'],
                humanize.naturalsize(data['downloaded']),
                humanize.naturalsize(data['total'])
            )
            Progress.set_label(label)
            Progress.set_value(data['downloaded'] / data['total'] * 100)

        if self._latest_release:

            logger.debug('downloading latest release asset')

            assert isinstance(self._latest_release, _Release)
            assets = self._latest_release.assets

            logger.debug('found {} assets'.format(len(assets)))

            for asset in assets:

                logger.debug('checking asset: {}'.format(asset.name))

                if asset.name.lower() == self._asset_filename.lower():

                    Progress.start('Downloading latest version', 100, '')
                    d = Downloader(
                        url=asset.browser_download_url,
                        filename='./update',
                        progress_hooks=[_progress_hook],
                    )
                    if d.download():
                        self._update_ready_to_install = True

        else:

            logger.debug('no release to download')

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

            logger.debug('no update to install')

            if self._cancel_update_func:
                self._cancel_update_func()

    def _version_check_follow_up(self, new_version_found: bool):

        if new_version_found:
            logger.debug('new version found, proceeding')

            self.pool.queue_task(self._process_candidates, _err_callback=self._cancel_update_func)
            self.pool.queue_task(self._download_latest_release, _err_callback=self._cancel_update_func)
            self.pool.queue_task(self._install_update, _err_callback=self._cancel_update_func)

    def version_check(self, channel: str):

        self.pool.queue_task(
            task=self._version_check,
            kwargs=dict(
                channel=channel
            ),
            _task_callback=self._version_check_follow_up,
            _err_callback=self._cancel_update_func)
