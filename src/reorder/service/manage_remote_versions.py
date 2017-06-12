# coding=utf-8

import urllib.parse

from src.misc import downloader
from src.reorder.finder import FindProfile, FindBranch, FindRemoteVersion
from src.reorder.service import ConvertUrl
from src.reorder.value import AVProbeResult, RemoteVersion
from src.ui.base import box_question
from src.utils import Progress
from src.utils import make_logger, ThreadPool, Path
from src.utils.av import AVSession

logger = make_logger(__name__)


class ManageRemoteVersions:
    _WATCHERS = []
    _POOL = ThreadPool(1, 'ManageRemoteVersion', _daemon=True)

    @staticmethod
    def watch_remote_version_change(func: callable):
        ManageRemoteVersions._WATCHERS.append(func)

    @staticmethod
    def notify_watchers():
        for func in ManageRemoteVersions._WATCHERS:
            func()

    @staticmethod
    def _get_build(branch: str):
        owner, repo = ConvertUrl.convert_av_url(FindProfile.get_active_profile().av_repo)
        if branch == 'All':
            return AVSession().get_last_build(owner, repo)
        else:
            branch = urllib.parse.quote(branch, safe='')
            return AVSession().get_latest_build_on_branch(owner, repo, branch)

    @staticmethod
    def _get_latest_remote_version(branch: str = 'All'):
        RemoteVersion.LATEST_REMOTE_VERSION = None
        build = ManageRemoteVersions._get_build(branch)
        if build:
            logger.debug(f'latest build found on Appveyor: {build.build.version.raw_version_str}')
            jobs = build.build.jobs.successful_only()
            if not jobs:
                raise RuntimeError('something')
            job = list(jobs)[0]
            artifacts = AVSession().get_artifacts(job.jobId)
            if not artifacts:
                raise RuntimeError('another something')
            artifact = artifacts[0]
            RemoteVersion.LATEST_REMOTE_VERSION = AVProbeResult(
                version=build.build.version.raw_version_str,
                branch=build.build.branch,
                download_url=f'https://ci.appveyor.com/api/buildjobs/{job.jobId}/artifacts/{artifact.fileName}',
                remote_file_size=artifact.size,
                remote_file_name=artifact.fileName,
            )

    @staticmethod
    def get_latest_remote_version():
        def task_callback(*_):
            ManageRemoteVersions.notify_watchers()

        branch = FindBranch.get_active_branch().name

        ManageRemoteVersions._POOL.queue_task(
            ManageRemoteVersions._get_latest_remote_version,
            kwargs=dict(branch=branch),
            _task_callback=task_callback,
        )

    @staticmethod
    def download_latest_remote_version(ui_parent=None):

        def task_callback(*_):
            Progress.done()

        latest = FindRemoteVersion.get_latest()
        profile = FindProfile.get_active_profile()

        if latest and profile:

            local_file = Path(profile.src_folder).joinpath(latest.remote_file_name).abspath()

            if local_file.exists():
                if not box_question(ui_parent, 'Local file already exists; do you want to overwrite?'):
                    return

            Progress.start(
                'Downloading {}'.format(latest.download_url.split('/').pop()),
                length=100,
                label=latest.remote_file_name
            )

            ManageRemoteVersions._POOL.queue_task(
                downloader.download,
                kwargs=dict(
                    url=latest.download_url,
                    local_file=local_file,
                    file_size=latest.remote_file_size,
                ),
                _task_callback=task_callback,
            )
