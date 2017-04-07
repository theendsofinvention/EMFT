# coding=utf-8

import requests
from utils import make_logger

logger = make_logger(__name__)

base_url = r'https://ci.appveyor.com/api'


def __url(*params):
    return '/'.join([base_url] + [p for p in params])


def get_latest_remote_version(branch='All'):
    logger.debug('querying AV for latest version')
    if branch == 'All':
        req = requests.get(
            __url('projects', '132nd-Entropy', '132nd-virtual-wing-training-mission-tblisi'),
        )
    else:
        req = requests.get(
            __url('projects', '132nd-Entropy', '132nd-virtual-wing-training-mission-tblisi', 'branch', branch),
        )
    latest = req.json()['build']['version']
    branch = req.json()['build']['branch']
    logger.debug('latest version found on AV: {}'.format(latest))
    return latest, branch


def latest_version_download_url(branch='All'):
    logger.debug('querying AV for latest version download url')
    if branch == 'All':
        req = requests.get(
            __url('projects', '132nd-Entropy', '132nd-virtual-wing-training-mission-tblisi'),
        )
    else:
        req = requests.get(
            __url('projects', '132nd-Entropy', '132nd-virtual-wing-training-mission-tblisi', 'branch', branch),
        )
    dl_url = r'https://ci.appveyor.com/api/buildjobs/{}/artifacts/TRMT_{}.miz'.format(
        req.json()['build']['jobs'][0]['jobId'], req.json()['build']['version'])
    logger.debug('latest version download url: {}'.format(dl_url))
    local_file_name = 'TRMT_{}.miz'.format(req.json()['build']['version'])
    logger.debug('local file name: {}'.format(local_file_name))
    return dl_url, local_file_name
