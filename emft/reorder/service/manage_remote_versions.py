# coding=utf-8

import urllib.parse

from emft.misc import downloader
from emft.reorder.finder import FindProfile, FindBranch, FindRemoteVersion
from emft.reorder.service import ConvertUrl
from emft.reorder.value import AVProbeResult, RemoteVersion
from emft.ui.base import box_question
from emft.utils import Progress
from emft.utils import make_logger, ThreadPool, Path
from emft.utils.av import AVSession

LOGGER = make_logger(__name__)


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
            LOGGER.debug(f'latest build found on Appveyor: {build.build.version}')
            jobs = build.build.jobs.successful_only()
            if not jobs:
                raise RuntimeError('something')
            job = list(jobs)[0]
            artifacts = AVSession().get_artifacts(job.jobId)
            if not artifacts:
                raise RuntimeError('another something')
            artifact = artifacts[0]
            RemoteVersion.LATEST_REMOTE_VERSION = AVProbeResult(
                version=build.build.version,
                branch=build.build.branch,
                download_url=f'https://ci.appveyor.com/api/buildjobs/{job.jobId}/artifacts/{artifact.fileName}',
                remote_file_size=artifact.size,
                remote_file_name=artifact.fileName,
            )

    @staticmethod
    def get_latest_remote_version():
        def task_callback(*_):
            ManageRemoteVersions.notify_watchers()

        branch = FindBranch.get_active_branch()

        if branch:
            ManageRemoteVersions._POOL.queue_task(
                ManageRemoteVersions._get_latest_remote_version,
                kwargs=dict(branch=branch.name),
                _task_callback=task_callback,
            )

        else:
            LOGGER.error('no active branch found')

    @staticmethod
    def download_latest_remote_version(ui_parent=None):

        def task_callback(*_):
            Progress.done()

        latest = FindRemoteVersion.get_latest()
        profile = FindProfile.get_active_profile()
        branch = FindBranch.get_active_branch().name

        if latest and profile and branch:

            local_file = Path(profile.src_folder).joinpath(latest.remote_file_name).abspath()

            if local_file.exists():
                if not box_question(ui_parent, 'Local file already exists; do you want to overwrite?'):
                    return

            ManageRemoteVersions._POOL.queue_task(
                downloader.download,
                kwargs=dict(
                    url=latest.download_url,
                    local_file=local_file,
                    file_size=latest.remote_file_size,
                ),
                _task_callback=task_callback,
            )
