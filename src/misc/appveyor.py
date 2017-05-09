# coding=utf-8

import humanize
import requests
from collections import namedtuple
from utils import make_logger

logger = make_logger(__name__)

base_url = r'https://ci.appveyor.com/api'


AVResult = namedtuple('AVResult', 'version branch download_url file_size file_name')


def __url(*params):
    return '/'.join([base_url] + [p for p in params])


def get_latest_remote_version(branch='All') -> AVResult:
    logger.debug('querying AV for latest version')
    if branch == 'All':
        req = requests.get(
            __url(
                'projects',
                '132nd-Entropy',
                '132nd-virtual-wing-training-mission-tblisi'
            ),
        )
    else:
        req = requests.get(
            __url(
                'projects',
                '132nd-Entropy',
                '132nd-virtual-wing-training-mission-tblisi',
                'branch',
                branch),
        )

    if not req.ok:
        logger.error('request failed')
        return

    latest = req.json()['build']['version']
    branch = req.json()['build']['branch']
    logger.debug('latest version found on AV: {}'.format(latest))

    job_id = req.json()['build']['jobs'][0]['jobId']
    build_version = req.json()['build']['version']

    logger.debug('jobId: {}\t\tbuild version: {}'.format(job_id, build_version))

    logger.debug('requesting artifacts list')

    artifacts_req = requests.get(
        __url(
            'buildjobs',
            job_id,
            'artifacts'
        ),
    )

    if not artifacts_req.ok:
        logger.error('failed to retrieve the list of artifacts for this build')
        return

    artifacts = artifacts_req.json()

    assert len(artifacts) == 1, artifacts

    trmt = artifacts[0]

    assert trmt['name'] == 'TRMT'
    assert trmt['type'] == 'File'

    file_name = trmt['fileName']
    file_size = trmt['size']

    logger.debug('File name: {}\t\tFile size: {}'.format(file_name, humanize.naturalsize(file_size)))

    dl_url = r'https://ci.appveyor.com/api/buildjobs/{}/artifacts/{}'.format(
        job_id, file_name
    )

    logger.debug('download url: {}'.format(dl_url))

    local_file_name = 'TRMT_{}.miz'.format(build_version)

    logger.debug('local file name: {}'.format(local_file_name))

    return AVResult(version=latest, branch=branch, download_url=dl_url, file_size=file_size, file_name=local_file_name)
