# coding=utf-8

import time

from src.ui.main_ui_interface import I
from src.utils import Downloader, make_logger

logger = make_logger(__name__)


def download(url, local_file, file_size: int = None):
    logger.info('downloading {} -> {}'.format(url, local_file))

    def hook(data):
        I.progress_set_value(int(float(data['percent_complete'])))

    time.sleep(1)
    dl = Downloader(
        url=url,
        filename=local_file,
        progress_hooks=[hook],
        content_length=file_size,
    )
    return dl.download()
