import humanize
import requests

from src.utils import make_logger
from .av_probe_result import AVProbeResult

logger = make_logger(__name__)


class RemoteAVRepo:
    def __init__(self, repo_owner: str, repo_name: str):
        self._repo_name = repo_name
        self._repo_owner = repo_owner
        self._latest_version = None
        self._branch = None
        self._artifact = None
        self._job_id = None
        self._build_version = None

    @property
    def repo_name(self):
        return self._repo_name

    @property
    def repo_owner(self):
        return self._repo_owner

    @property
    def __base_url(self):
        return r'https://ci.appveyor.com/api'

    @property
    def latest_version(self) -> str:
        return self._latest_version

    @property
    def branch(self) -> str:
        return self._branch

    @staticmethod
    def _send_request(request_url: str) -> dict:

        req = requests.get('/'.join(request_url))

        if not req.ok:
            msg = (f'request failed: {req.status_code}\n'
                   'Reason: {req.reason}\n'
                   'Text: {req.text}\n'
                   'Url: {req.url}')
            logger.error(msg)
            from src.sentry import SENTRY
            SENTRY.captureMessage(msg)
            raise ConnectionError(req.reason)

        return req.json()

    def get_latest_remote_version(self, branch: str = 'All'):
        url_params = [
            self.__base_url,
            'projects',
            self._repo_owner,
            self._repo_name,
        ]
        if branch != 'All':
            url_params.append('branch')
            url_params.append(branch)

        build = self._send_request('/'.join(url_params))['build']

        self._latest_version = build['version']
        self._branch = build['branch']
        self._job_id = build['jobs'][0]['jobId']
        self._build_version = build['version']
        logger.debug(f'latest version found on AV: {self._latest_version}')

    def get_artifacts(self):
        if self._job_id is None:
            raise RuntimeError('must scan for latest version first')

        url_params = (
            self.__base_url,
            'buildjobs',
            self._job_id,
            'artifacts',
        )

        artifacts = self._send_request('/'.join(url_params))

        if not artifacts:
            raise ValueError(f'no artifact found\n{artifacts}')

        d = artifacts[0]

        remote_file_name = d['fileName']
        remote_file_size = d['size']

        logger.debug(f'file name: {remote_file_name}\t\t size: {humanize.naturalsize(remote_file_size)}')

        download_url = f'https://ci.appveyor.com/api/buildjobs/{self._job_id}/artifacts/{remote_file_name}'

        logger.debug(f'download url: {download_url}')

        local_file_name = f'TRMT_{self._build_version}.miz'

        logger.debug(f'local file name: {local_file_name}')

        return AVProbeResult(
            version=self.latest_version,
            branch=self.branch,
            download_url=download_url,
            remote_file_name=remote_file_name,
            remote_file_size=remote_file_size,
        )
