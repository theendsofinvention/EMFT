# coding=utf-8

import abc
import io
import re
import subprocess
from collections import UserDict

import humanize
import semver

from src.utils.av import AVSession, AVBuild
from src.utils.custom_logging import make_logger
from src.utils.custom_path import Path
from src.utils.downloader import Downloader
from src.utils.gh import GHRelease, GHSession
from src.utils.monkey import nice_exit
from src.utils.progress import Progress
from src.utils.threadpool import ThreadPool
from src.sentry import SENTRY

logger = make_logger(__name__)


class Channel:
    valid_channels = [
        'alpha',
        'beta',
        'dev',
        'rc',
        'hotfix',
        'stable',
    ]

    def __new__(cls, channel_name):
        if isinstance(channel_name, Channel):
            return channel_name
        return super(Channel, cls).__new__(cls)

    def __init__(self, channel_name: str):
        if channel_name not in self.valid_channels or not isinstance(channel_name, str):
            raise ValueError('Invalid channel name: {}'.format(channel_name))
        channel_name = channel_name.lower()
        self._channel_name = channel_name

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def _value(self):
        return self.valid_channels.index(self.channel_name)

    def __str__(self):
        return self.channel_name

    def __eq__(self, other: 'Channel'):
        return self._value == other._value

    def __gt__(self, other: 'Channel'):
        return self._value > other._value

    def __lt__(self, other: 'Channel'):
        return self._value < other._value

    def __ge__(self, other: 'Channel'):
        return self._value >= other._value

    def __le__(self, other: 'Channel'):
        return self._value <= other._value


class Version:
    re_branch = re.compile(r'.*\.(?P<branch>.*)\..*?')

    def __new__(cls, version_str):
        if isinstance(version_str, Version):
            return version_str
        return super(Version, cls).__new__(cls)

    def __init__(self, version_str: str):
        try:
            semver.parse(version_str)
        except ValueError:
            raise ValueError(version_str)
        self._version_str = version_str
        self._channel = None
        self._branch = None

        self._parse()

    def _parse(self):
        info = semver.parse_version_info(self._version_str)
        if info.prerelease is None:
            self._channel = Channel('stable')
        elif info.prerelease.startswith('alpha.'):
            self._channel = Channel('alpha')
            self._branch = self.re_branch.match(info.prerelease).group('branch')
        elif info.prerelease.startswith('beta.'):
            self._channel = Channel('beta')
            self._branch = self.re_branch.match(info.prerelease).group('branch')
        elif info.prerelease.startswith('dev'):
            self._channel = Channel('dev')
        elif info.prerelease.startswith('rc'):
            self._channel = Channel('rc')
        else:
            raise ValueError(info.prerelease)

    @property
    def branch(self) -> str or None:
        return self._branch

    @property
    def channel(self) -> Channel:
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


class DownloadableAsset:
    def __init__(self, url, size):
        self.url = url
        self.size = size


class AbstractRelease(abc.ABC):
    def __new__(cls, release):
        if isinstance(release, AbstractRelease):
            return release
        return super(AbstractRelease, cls).__new__(cls)

    @property
    @abc.abstractmethod
    def version(self) -> Version:
        """"""

    @property
    @abc.abstractmethod
    def branch(self) -> str:
        """"""

    @property
    @abc.abstractmethod
    def changelog(self) -> str:
        """"""

    @property
    @abc.abstractmethod
    def channel(self) -> Channel:
        """"""


class AVRelease(AbstractRelease):
    @property
    def version(self) -> Version:
        return self._version

    @property
    def _has_asset(self) -> bool:
        return self.build.jobs[0].artifactsCount > 0

    @property
    def channel(self) -> Channel:
        return self.version.channel

    @property
    def branch(self) -> str:
        return self.version.branch

    @property
    def changelog(self):
        changelog = self.build.message
        if self.build.messageExtended:
            changelog += '\n\n' + str(self.build.messageExtended)
        return changelog

    def __init__(self, build: AVBuild):
        self.build = build
        self._version = Version(self.build.version.version_str)


class GithubRelease(AbstractRelease):
    def __init__(self, gh_release: GHRelease):
        self._gh_release = gh_release
        self._version = Version(self._gh_release.tag_name)

    @property
    def gh_release(self) -> GHRelease:
        return self._gh_release

    @property
    def version(self):
        return self._version

    @property
    def assets(self):
        return self._gh_release.assets

    @property
    def channel(self) -> Channel:
        return self._version.channel

    @property
    def branch(self) -> str or None:
        return self._version.branch

    @property
    def changelog(self) -> str:
        return self._gh_release.body


class AvailableReleases(UserDict):
    def add(self, release: AbstractRelease):
        if not isinstance(release, AbstractRelease):
            raise TypeError('expected GithubRelease, got: {}'.format(type(release)))
        self.data[release.version.version_str] = release

    def __setitem__(self, *_):
        raise NotImplementedError

    def filter_by_channel(self, channel: str or Channel) -> 'AvailableReleases' or None:

        channel = Channel(channel)

        ret = AvailableReleases()

        if len(self) == 0:
            logger.error('no available release')
            return ret

        for release in self.values():

            if release.version.channel < channel:
                logger.debug('skipping release on channel: {} ({})'.format(
                    release.version.channel, release.version.version_str))
                continue

            ret.add(release)

        return ret

    def filter_by_branch(self, branch: str or Version) -> 'AvailableReleases' or None:

        if isinstance(branch, Version):
            branch = branch.branch

        ret = AvailableReleases()

        for release in self.values():

            if release.branch and not branch == release.branch:
                logger.debug('skipping different branch; own: {} remote: {}'.format(
                    branch, release.branch
                ))
                continue

            ret.add(release)

        return ret

    def filter_from_version(self, version: Version or str) -> 'AvailableReleases' or None:

        version = Version(version)

        return self.filter_by_channel(version.channel).filter_by_branch(version.branch)

    def get_latest_release(self) -> AbstractRelease or None:

        if len(self) == 0:
            logger.error('no release available')
            return

        latest = Version('0.0.0')

        for rel in self.values():
            assert isinstance(rel, AbstractRelease)
            if rel.version > latest:
                latest = rel.version

        return self.data[latest.version_str]


class BaseUpdater(abc.ABC):
    def __init__(self):
        self._available = AvailableReleases()

        self.pool = ThreadPool(_num_threads=1, _basename='updater', _daemon=True)

    @abc.abstractmethod
    def release_has_assets(self, release: AbstractRelease) -> bool:
        """"""

    @abc.abstractmethod
    def get_downloadable_asset(self, release: AbstractRelease) -> DownloadableAsset:
        """"""

    @staticmethod
    def _install_update(executable: Path) -> bool or None:
        logger.debug('installing update')
        # noinspection SpellCheckingInspection
        bat_liiiiiiiiiiiines = [  # I'm deeply sorry ...
            '@echo off',
            'echo Updating to latest version...',
            'ping 127.0.0.1 - n 5 - w 1000 > NUL',
            'move /Y "update" "{}" > NUL'.format(executable.basename()),
            'echo restarting...',
            'start "" "{}"'.format(executable.basename()),
            'DEL update.vbs',
            'DEL "%~f0"',
        ]
        logger.debug('write bat file')
        with io.open('update.bat', 'w', encoding='utf-8') as bat:
            bat.write('\n'.join(bat_liiiiiiiiiiiines))

        logger.debug('write vbs script')
        with io.open('update.vbs', 'w', encoding='utf-8') as vbs:
            # http://www.howtogeek.com/131597/can-i-run-a-windows-batch-file-without-a-visible-command-prompt/
            vbs.write('CreateObject("Wscript.Shell").Run """" '
                      '& WScript.Arguments(0) & """", 0, False')
        logger.debug('starting update batch file')
        args = ['wscript.exe', 'update.vbs', 'update.bat']
        subprocess.Popen(args)
        nice_exit(0)

        return True  # for testing purpose

    @property
    @abc.abstractmethod
    def _release_caster(self) -> callable:
        """Base class used to instantiate releases"""

    @abc.abstractmethod
    def _contact_remote_host_for_available_releases(self) -> list:
        """"""

    def _gather_available_releases(self):

        self._available = AvailableReleases()

        releases = self._contact_remote_host_for_available_releases()

        if releases:
            logger.debug('found {} available releases'.format(len(releases)))
            for rel in releases:

                try:
                    # noinspection PyCallingNonCallable
                    rel = self._release_caster(rel)
                    assert isinstance(rel, AbstractRelease)
                    self._available.add(rel)
                except ValueError:
                    logger.exception('skipping badly formatted release')
                    continue

                # logger.debug('release found: {} ({})'.format(rel.version, rel.channel))

            return len(self._available) > 0

        else:
            logger.error('no release found')

    def _get_latest_release(self, channel: str = 'stable', branch: str = None):
        self._gather_available_releases()
        return self._available.filter_by_channel(channel).filter_by_branch(branch).get_latest_release()

    def get_latest_release(
            self,
            channel: str = 'stable',
            branch: str = None,
            success_callback: callable = None,
            failure_callback: callable = None,
    ):
        self.pool.queue_task(
            task=self._get_latest_release,
            kwargs=dict(
                channel=channel,
                branch=branch,
            ),
            _task_callback=success_callback,
            _err_callback=failure_callback
        )

    def _download_asset(
            self,
            release: AbstractRelease,
            *,
            extra_label: str = None,
            hexdigest=None,
            download_retries: int = 3,
            block_size: int = 4096,
            progress_hooks: callable = None,
            hash_method: str = 'md5'
    ) -> bool:
        """"""

        def _progress_hook(data):
            label = 'Time left: {} ({}/{})'.format(
                data['time'],
                humanize.naturalsize(data['downloaded']),
                humanize.naturalsize(data['total'])
            )
            if extra_label:
                label = '{}\n\n{}'.format(extra_label, label)
            Progress.set_label(label)
            Progress.set_value(data['downloaded'] / data['total'] * 100)

        if progress_hooks is None:
            progress_hooks = _progress_hook
        if self.release_has_assets(release):
            asset = self.get_downloadable_asset(release)

            Progress.start(
                title='Downloading update - {}'.format(release.version.version_str),
            )

            return Downloader(
                url=asset.url,
                filename='./update',
                content_length=asset.size,
                hexdigest=hexdigest,
                download_retries=download_retries,
                block_size=block_size,
                progress_hooks=[progress_hooks],
                hash_method=hash_method
            ).download()
        else:
            logger.error('release has no asset')

    def _download_and_install_release(
            self,
            release: AbstractRelease,
            executable_path: str or Path,
            extra_label: str = None
    ):

        if self._download_asset(release, extra_label=extra_label):

            executable_path = Path(executable_path)

            if not executable_path.exists():
                logger.error('executable not found: {}'.format(executable_path.abspath()))

            else:
                if self._install_update(executable_path):
                    return True

    def download_and_install_release(
            self,
            release: AbstractRelease,
            executable_path: str or Path = None,
            success_callback=None,
            failure_callback=None
    ):

        logger.info('queuing release download and installation')

        self.pool.queue_task(
            self._download_and_install_release,
            kwargs=dict(
                release=release,
                executable_path=executable_path,
            ),
            _task_callback=success_callback,
            _err_callback=failure_callback,
        )

    def _find_and_install_latest_release(
            self,
            current_version: str or Version,
            executable_path: str or Path,
            *,
            extra_label: str = None,
            channel: str = 'stable',
            branch: str or Version = None,
            cancel_update_hook: callable = None,
            pre_update_hook: callable = None,
            no_new_version_hook: callable = None,
            no_candidates_hook: callable = None
    ):

        def cancel_update():

            logger.debug('cancelling update')

            if cancel_update_hook:

                logger.debug('running cancel hook')
                cancel_update_hook()

        def no_new_version():

            logger.debug('no new version found')

            if no_new_version_hook:

                logger.debug('calling no new version hook')
                no_new_version_hook()

        def no_candidates():

            logger.debug('no candidate found')

            if no_candidates_hook:

                logger.debug('calling no candidate hook')
                no_candidates_hook()

        self._gather_available_releases()

        try:
            current_version = Version(current_version)
        except ValueError:
            error = f'could no parse version: {current_version}'
            SENTRY.captureMessage(error)
            logger.exception(error)
            return

        if branch is None:
            branch = current_version.branch

        candidates = self._available.filter_by_channel(channel)
        candidates = candidates.filter_by_branch(branch)

        if not candidates:
            logger.info('no new version found')
            return no_candidates()

        else:

            latest_rel = candidates.get_latest_release()

            if latest_rel:  # pragma: no branch

                assert isinstance(latest_rel, AbstractRelease)

                logger.debug('latest available release: {}'.format(latest_rel.version))

                if latest_rel.version > current_version:

                    logger.debug('this is a newer version, updating')

                    if pre_update_hook:

                        if not pre_update_hook():
                            logger.error('pre-update hook returned False, cancelling update')
                            return cancel_update()

                    if self._download_and_install_release(latest_rel, executable_path, extra_label):
                        return True

                    else:
                        return cancel_update()

                else:
                    return no_new_version()

    def find_and_install_latest_release(
            self,
            current_version: str or Version,
            executable_path: str or Path,
            *,
            channel: str = 'stable',
            branch: str or Version = None,
            cancel_update_hook: callable = None,
            pre_update_hook: callable = None,
            failure_callback: callable = None,
            success_callback: callable = None
    ):
        self.pool.queue_task(
            self._find_and_install_latest_release,
            kwargs=dict(
                current_version=current_version,
                channel=channel,
                branch=branch,
                cancel_update_hook=cancel_update_hook,
                pre_update_hook=pre_update_hook,
                executable_path=executable_path,
            ),
            _task_callback=success_callback,
            _err_callback=failure_callback,
        )


class GHUpdater(BaseUpdater):
    def release_has_assets(self, release: GithubRelease) -> bool:
        return len(release.gh_release.assets) > 0

    def get_downloadable_asset(self, release: GithubRelease) -> DownloadableAsset:
        return DownloadableAsset(
            release.gh_release.assets[0].browser_download_url,
            release.gh_release.assets[0].size
        )

    def _contact_remote_host_for_available_releases(self) -> list:
        logger.debug('querying GH API for available releases')
        releases = GHSession().get_all_releases(self._gh_user, self._gh_repo)
        return releases

    @property
    def _release_caster(self):
        return GithubRelease

    def __init__(
            self,
            gh_user: str,
            gh_repo: str,
    ):
        """
        :param gh_user: Github user name
        :param gh_repo: Github repo name
        """
        super(GHUpdater, self).__init__()
        self._gh_user = gh_user
        self._gh_repo = gh_repo


class AVUpdater(BaseUpdater):
    def _get_artifacts(self, release):
        if release.version.version_str not in self.__artifacts:
            build = AVSession().get_build_by_version(
                self._av_user, self._av_project, release.build.version.url_safe_version_str
            )
            job_id = build.build.jobs[0].jobId
            self.__artifacts[release.version.version_str] = (AVSession().get_artifacts(job_id), job_id)
        return self.__artifacts[release.version.version_str]

    def release_has_assets(self, release: AVRelease) -> bool:
        artifacts, _ = self._get_artifacts(release)
        return len(artifacts) > 0

    def get_downloadable_asset(self, release: AVRelease) -> DownloadableAsset:
        artifacts, job_id = self._get_artifacts(release)
        return DownloadableAsset(
            r'https://ci.appveyor.com/api/buildjobs/{}/artifacts/{}'.format(job_id, artifacts[0].url_safe_file_name),
            artifacts[0].size,
        )

    @property
    def _release_caster(self) -> callable:
        return AVRelease

    def _contact_remote_host_for_available_releases(self) -> list:
        return list(AVSession().get_history(self._av_user, self._av_project).builds.successful_only())

    def __init__(
            self,
            av_user: str,
            av_project: str,
    ):
        """
        :param av_user: AppVeyor user name
        :param av_project: AppVeyor repo name
        """
        super(AVUpdater, self).__init__()
        self._av_user = av_user
        self._av_project = av_project
        self.__artifacts = {}
