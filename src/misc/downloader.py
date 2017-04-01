# coding=utf-8

from utils import Progress, Downloader, make_logger

logger = make_logger(__name__)


def download(url, local_file, progress_title):
    logger.info('downloading {} -> {}'.format(url, local_file))

    Progress.start(progress_title)

    def hook(data):
        Progress.set_value(float(data['percent_complete']))

    dl = Downloader(
        url=url,
        filename=local_file,
        progress_hooks=[hook])

    dl.download()
