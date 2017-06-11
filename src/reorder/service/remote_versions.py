# coding=utf-8

import urllib.parse

from src.reorder.service import ManageProfiles
from src.reorder.value import AVProbeResult
from src.utils import make_logger
from src.utils.av import AVSession

logger = make_logger(__name__)


class RemoteVersions:
    @staticmethod
    def _get_build(branch: str):
        owner, repo = ManageProfiles.get_av_repo_info()
        if branch == 'All':
            return AVSession().get_last_build(owner, repo)
        else:
            branch = urllib.parse.quote(branch, safe='')
            return AVSession().get_latest_build_on_branch(owner, repo, branch)

    @staticmethod
    def get_latest_remote_version(branch: str = 'All') -> AVProbeResult:
        build = RemoteVersions._get_build(branch)
        if build:
            logger.debug(f'latest build found on Appveyor: {build.build.version}')
            jobs = build.build.jobs.successful_only()
            if not jobs:
                raise RuntimeError('something')
            job = list(jobs)[0]
            artifacts = AVSession().get_artifacts(job.jobId)
            if not artifacts:
                raise RuntimeError('another something')
            artifact = artifacts[0]
            return AVProbeResult(
                version=build.build.version.raw_version_str,
                branch=build.build.branch,
                download_url=f'https://ci.appveyor.com/api/buildjobs/{job.jobId}/artifacts/{artifact.fileName}',
                remote_file_size=artifact.size,
                remote_file_name=artifact.fileName,
            )
