# coding=utf-8

from utils import Progress, Downloader, make_logger

logger = make_logger(__name__)


def download(url, local_file, progress_title: str, progress_text: str = '', file_size: int = None):
    logger.info('downloading {} -> {}'.format(url, local_file))

    Progress.start(progress_title)
    Progress.set_label(progress_text)

    def hook(data):
        Progress.set_value(float(data['percent_complete']))

    dl = Downloader(
        url=url,
        filename=local_file,
        progress_hooks=[hook],
        content_length=file_size,
    )

    return dl.download()
