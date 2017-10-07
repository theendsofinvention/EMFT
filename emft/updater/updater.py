# coding=utf-8
import io
import os
import subprocess
import typing

from transitions import EventData, Machine

from emft.core import downloader, nice_exit
from emft.core.logging import make_logger
from emft.core.properties import WatchedProperty
from emft.core.providers.appveyor import AVBuild, AVSession  # noqa: F401
from emft.core.threadpool import ThreadPool
from emft.updater import channel
from .customspec import CustomSpec
from .customversion import CustomVersion

LOGGER = make_logger(__name__)


class DownloadableAsset:
    def __init__(self, url, size):
        self.url = url
        self.size = size

    def __str__(self):
        return self.url


# TODO: try again, ignoring a few faulty versions
class Updater(Machine):
    def __init__(self, current_version: str, av_user: str, av_repo: str, local_executable: str, channel: str, **_):
        Machine.__init__(
            self,
            states=[
                'initial',
                'collecting',
                'parsing',
                'downloading',
                'installing',
                'waiting',
            ],
            auto_transitions=False,
            send_event=True,
            prepare_event=self._prepare_event,
            finalize_event=self._finalize_event,
            after_state_change=self._after_state_change,
        )
        # noinspection PyTypeChecker
        self.add_transition(
            trigger='look_for_new_version',
            source=['waiting', 'initial'],
            dest='collecting',
            before=[
                '_reset_internal_values',
                '_make_busy',
            ],
            after='_collect_available_releases',
            conditions='_is_ready',
        )
        self.add_transition(
            trigger='parse_av_builds',
            source='*',
            dest='parsing',
            after='_parse_available_releases',
        )
        self.add_transition(
            trigger='end_of_parsing',
            source='parsing',
            dest='waiting',
            unless='_should_auto_update',
            after='_make_ready',
        )
        self.add_transition(
            trigger='end_of_parsing',
            source='parsing',
            dest='downloading',
            conditions='_should_auto_update',
            after='_download_latest_version',
        )
        self.add_transition(
            trigger='download',
            source='*',
            dest='downloading',
            conditions='_is_ready_to_download',
            after='_download_latest_version',
        )
        self.add_transition(
            trigger='install',
            source='*',
            dest='installing',
            conditions='_is_ready_to_install',
            after='_install_latest_version',
        )

        self._channel = channel
        self._av_user, self._av_repo = av_user, av_repo
        self._pool = ThreadPool(_num_threads=1, _basename='updater', _daemon=True)

        self._auto_update = False
        try:
            self._current_version = CustomVersion(current_version)
        except ValueError:
            LOGGER.error(current_version)
            raise
        self._spec = CustomSpec(f'>={str(self._current_version.to_spec())}')
        self._local_executable = local_executable
        self._hexdigest = None
        self._av_builds = dict()
        self._asset = None
        self.is_ready = True

    @property
    def current_version(self) -> CustomVersion:
        return self._current_version

    @WatchedProperty(default_value=None)
    def latest_version(self, value) -> typing.Union['CustomVersion', None]:
        """
        Latest remote version found
        """
        return value

    @WatchedProperty(default_value=False)
    def is_ready(self, value) -> bool:
        """
        Will be true is the updater is ready to accept a new job
        """
        return value

    @property
    def av_builds(self) -> typing.Dict['CustomVersion', 'AVBuild']:
        return self._av_builds

    @property
    def asset(self) -> typing.Union['DownloadableAsset', None]:
        return self._asset

    def _make_ready(self, event: EventData):
        LOGGER.debug(f'from {event.event.name}')
        self.is_ready = True

    def _make_busy(self, event: EventData):
        LOGGER.debug(f'from {event.event.name}')
        self.is_ready = False

    # noinspection PyMethodMayBeStatic
    def _prepare_event(self, event: EventData):
        LOGGER.debug(f'from: {event.event.name}({event.kwargs}): start: state: {self.state}')

    # noinspection PyMethodMayBeStatic
    def _finalize_event(self, event: EventData):
        if event.error:
            LOGGER.warning(f'from: {event.event.name}({event.kwargs}): error: {type(event.error)}: {event.error}')
        else:
            LOGGER.debug(f'from: {event.event.name}({event.kwargs}): done:  state: {self.state}')

    # noinspection PyMethodMayBeStatic
    def _after_state_change(self, event: EventData):
        LOGGER.debug(f'state change: "{self.state}" triggered by {event.event.name}')

    def _has_new_version(self, event: EventData) -> bool:
        result = bool(self.latest_version is not None)
        LOGGER.debug(f'from {event.event.name}: {result}')
        return result

    def _should_auto_update(self, event: EventData) -> bool:
        result = True
        if not self._auto_update:
            result = False
        if not self._has_new_version(event):
            LOGGER.debug('skipping auto-update: no new version')
            result = False
        elif not self.latest_version > self.current_version:
            LOGGER.debug('skipping auto-update: no newer version found')
            result = False
        LOGGER.debug(f'from {event.event.name}: {result}')
        return result

    def _is_ready(self, event: EventData) -> bool:
        LOGGER.debug(f'from {event.event.name}: {self.is_ready}')
        return self.is_ready

    # noinspection PyMethodMayBeStatic
    def _is_ready_to_download(self, event: EventData):
        result = True  # TODO
        LOGGER.debug(f'from {event.event.name}: {result}')
        return result

    # noinspection PyMethodMayBeStatic
    def _is_ready_to_install(self, event: EventData):
        result = True  # TODO
        LOGGER.debug(f'from {event.event.name}: {result}')
        return result

    def _reset_internal_values(self, event: EventData):
        LOGGER.debug(f'from: {event.event.name}: resetting internal values')
        self.latest_version = None
        self._av_builds = dict()
        self._asset = None
        self._hexdigest = None
        self._auto_update = event.kwargs.get('auto_update') or False

    def look_for_new_version(self, auto_update=False):
        pass

    def find_latest_version_on_channel(self, update_channel: str):
        if update_channel not in channel.VALID_CHANNELS:
            raise ValueError(f'invalid channel: {update_channel}')
        self._spec = CustomSpec(f'>0.0.0')
        self._channel = update_channel
        self.look_for_new_version()

    def install_latest_version(self):
        self.download()

    @staticmethod
    def _collect_releases_in_the_background(_av_user, _av_repo):
        result = dict()
        for av_build in AVSession().get_history(_av_user, _av_repo).builds.successful_only():
            try:
                version = CustomVersion.coerce(av_build.version)
            except TypeError:
                LOGGER.error(f'expected string or bytes-like object, got: {type(av_build.version)}')
                raise
            except ValueError:
                LOGGER.warning(f'skipping badly formatted version string: "{av_build.version}"')
                continue
            result[version] = av_build
        return result

    def _collect_available_releases(self, event: EventData):

        def _callback(result):
            LOGGER.debug(f'end of collection, got {len(result)} AV builds available')
            self._av_builds = result
            self.parse_av_builds()

        LOGGER.debug('start collection')
        self._auto_update = event.kwargs.get('auto_update', False)
        self._pool.queue_task(
            task=self._collect_releases_in_the_background,
            kwargs=dict(
                _av_user=self._av_user,
                _av_repo=self._av_repo,
            ),
            _task_callback=_callback
        )

    def _parse_available_releases(self, event: EventData):
        LOGGER.debug(f'from: {event.event.name}: parsing AV builds')

        available_versions = set(self.av_builds.keys())
        self.latest_version = self._spec.select_channel(available_versions, self._channel)

        def _get_hexdigest():
            # TODO hexdigest
            pass

        def _set_hexdigest(hexdigest):
            self._hexdigest = hexdigest

        if self.latest_version:
            LOGGER.debug(f'latest version found: {self.latest_version}')
            av_build = self.av_builds[self.latest_version]
            job_id = AVSession().get_build_by_version(
                self._av_user, self._av_repo, av_build.url_safe_version
            ).build.jobs[0].jobId

            for artifact in AVSession().get_artifacts(job_id):
                if artifact.name == 'hexdigest':
                    self._pool.queue_task(
                        task=_get_hexdigest,
                        _task_callback=_set_hexdigest,
                    )
                if artifact.name == 'emft':
                    self._asset = DownloadableAsset(
                        f'https://ci.appveyor.com/api/buildjobs/{job_id}/artifacts/{artifact.url_safe_file_name}',
                        artifact.size
                    )
        self.end_of_parsing()

    def _download_latest_version(self, event: EventData):

        def _download_in_the_background(url, size, hexdigest):
            return downloader.download(
                url=url,
                local_file='./update',
                file_size=size,
                hexdigest=hexdigest,
                title=f'Downloading EFMT {self.latest_version.to_short_string()}'
            )

        def _download_callback(download_successful):
            LOGGER.debug(f'download: {download_successful}')
            if download_successful:
                self.install()

        if self._asset:
            LOGGER.debug(f'from: {event.event.name}: downloading latest asset')
            self._pool.queue_task(
                task=_download_in_the_background,
                kwargs=dict(
                    url=self.asset.url,
                    size=self.asset.size,
                    hexdigest=self._hexdigest,
                ),
                _task_callback=_download_callback,
            )
        else:
            pass  # TODO

    # noinspection PyMethodMayBeStatic
    def _install_latest_version(self, event: EventData):
        LOGGER.debug(f'from: {event.event.name}: installing update')
        # noinspection SpellCheckingInspection
        bat_liiiiiiiiiiiines = [  # I'm deeply sorry ...
            '@echo off',
            'echo Updating to latest version...',
            'ping 127.0.0.1 -n 5 -w 1000 > NUL',
            f'move /Y "update" "{os.path.basename(self._local_executable)}" > NUL',
            'echo restarting...',
            f'start "" "{os.path.basename(self._local_executable)}"',
            'DEL update.vbs',
            'DEL "%~f0"',
        ]
        LOGGER.debug('write bat file')
        with io.open('update.bat', 'w', encoding='utf-8') as bat:
            bat.write('\n'.join(bat_liiiiiiiiiiiines))

        LOGGER.debug('write vbs script')
        with io.open('update.vbs', 'w', encoding='utf-8') as vbs:
            # http://www.howtogeek.com/131597/can-i-run-a-windows-batch-file-without-a-visible-command-prompt/
            vbs.write('CreateObject("Wscript.Shell").Run """" '
                      '& WScript.Arguments(0) & """", 0, False')
        LOGGER.debug('starting update batch file')
        args = ['wscript.exe', 'update.vbs', 'update.bat']
        subprocess.Popen(args)
        nice_exit()

        return True  # for testing purpose

    @WatchedProperty(default_value=None)
    def error(self, value):
        return value


updater = None
