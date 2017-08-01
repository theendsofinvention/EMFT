# coding=utf-8

import time

import humanize

from emft.utils import Downloader, make_logger
# from src.ui.main_ui_interface import I
from emft.utils import Progress

LOGGER = make_logger(__name__)


def download(
    url,
    local_file,
    file_size: int = None,
    hexdigest: str = None,
    title: str = '',
):
    LOGGER.info('downloading {} -> {}'.format(url, local_file))

    if not title:
        title = f'Downloading {url.split("/")[-1]}'

    Progress.start(
        title=title,
        label=f'Downloading to: {local_file}',
    )

    def _progress_hook(data):
        label = 'Time left: {} ({}/{})'.format(
            data['time'],
            humanize.naturalsize(data['downloaded']),
            humanize.naturalsize(data['total'])
        )
        Progress.set_label(label)
        Progress.set_value(data['downloaded'] / data['total'] * 100)

    # def hook(data):
    #     # I.progress_set_value(int(float(data['percent_complete'])))
    #     Progress().set_value(int(float(data['percent_complete'])))

    time.sleep(1)
    dl = Downloader(
        url=url,
        filename=local_file,
        progress_hooks=[_progress_hook],
        content_length=file_size,
        hexdigest=hexdigest
    )
    return dl.download()
