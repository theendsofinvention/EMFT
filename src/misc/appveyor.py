# coding=utf-8

import requests
from utils import make_logger

logger = make_logger(__name__)

base_url = r'https://ci.appveyor.com/api'


def __url(*params):
    return '/'.join([base_url] + [p for p in params])


def get_latest_remote_version():
    logger.debug('querying AV for latest version')
    req = requests.get(
        __url('projects', '132nd-Entropy', '132nd-virtual-wing-training-mission-tblisi'),
    )
    latest = req.json()['build']['version']
    logger.debug('latest version found on AV: {}'.format(latest))
    return latest


def latest_version_download_url():
    logger.debug('querying AV for latest version download url')
    req = requests.get(
        __url('projects', '132nd-Entropy', '132nd-virtual-wing-training-mission-tblisi'),
    )
    dl_url = r'https://ci.appveyor.com/api/buildjobs/{}/artifacts/TRMT_{}.miz'.format(
        req.json()['build']['jobs'][0]['jobId'], req.json()['build']['version'])
    logger.debug('latest version download url: {}'.format(dl_url))
    local_file_name = 'TRMT_{}.miz'.format(req.json()['build']['version'])
    logger.debug('local file name: {}'.format(local_file_name))
    return dl_url, local_file_name
