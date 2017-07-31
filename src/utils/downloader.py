# coding=utf-8

import hashlib
import time
import os

import certifi
import urllib3

from src.utils.custom_logging import make_logger
from src.utils.threadpool import ThreadPool

LOGGER = make_logger(__name__)


def get_hash(data, method: str = 'md5'):

    if not isinstance(data, bytes):
        data = bytes(data, 'utf-8')

    try:
        func = getattr(hashlib, method)
    except AttributeError:
        raise RuntimeError('cannot find method "{}" in hashlib'.format(method))
    else:
        hash_ = func(data).hexdigest()
        LOGGER.debug('hash for binary data: %s', hash_)

        return hash_


def get_http_pool():
    return urllib3.PoolManager(cert_reqs=str('CERT_REQUIRED'),
                               ca_certs=certifi.where())


class Downloader:
    def __init__(self,
                 url: str,
                 filename: str,
                 content_length: int = None,
                 hexdigest=None,
                 concurrent_download: int = 1,
                 download_retries: int = 3,
                 block_size: int = 4096 * 4,
                 progress_hooks: list = None,
                 hash_method: str = 'md5',
                 ):

        self.pool = ThreadPool(_num_threads=concurrent_download, _basename='download', _daemon=True)
        self.url = url
        self.filename = filename
        self.content_length = content_length
        self.max_download_retries = download_retries
        self.block_size = block_size
        self.http_pool = get_http_pool()
        self.hexdigest = hexdigest
        self.file_binary_data = None

        if progress_hooks is not None and not isinstance(progress_hooks, list):
            raise TypeError(type(progress_hooks))
        self.progress_hooks = progress_hooks or []

        self.hash_method = hash_method

    def _write_to_file(self):

        with open(self.filename, 'wb') as f:
            f.write(self.file_binary_data)

    def _check_hash(self):

        if self.hexdigest is None:
            LOGGER.debug('no hash to verify')
            return None

        if self.file_binary_data is None:
            LOGGER.debug('cannot verify file hash')
            return False

        LOGGER.debug('checking file hash')
        LOGGER.debug('update hash: %s', self.hexdigest)

        file_hash = get_hash(self.file_binary_data, self.hash_method)

        if file_hash == self.hexdigest:
            LOGGER.debug('file hash verified')
            return True

        LOGGER.debug('cannot verify file hash')
        return False

    @staticmethod
    def _calc_eta(start, now, total, current):

        if total is None:
            return '--:--'

        dif = now - start
        if current == 0 or dif < 0.001:
            return '--:--'

        rate = float(current) / dif
        eta = int((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)

        if eta_mins > 99:
            return '--:--'

        return '%02d:%02d' % (eta_mins, eta_secs)

    @staticmethod
    def _calc_progress_percent(received, total):

        if total is None:
            return '-.-%'

        percent = float(received) / total * 100
        percent = '%.1f' % percent

        return percent

    @staticmethod
    def _get_content_length(data):

        content_length = data.headers.get("Content-Length")

        if content_length is not None:
            content_length = int(content_length)

        LOGGER.debug('Got content length of: %s', content_length)

        return content_length

    @staticmethod
    def _best_block_size(time_, chunk: float):

        new_min = max(chunk / 2.0, 1.0)
        new_max = min(max(chunk * 2.0, 1.0), 4194304)  # Do not surpass 4 MB

        if time_ < 0.001:
            return int(new_max)

        rate = chunk / time_

        if rate > new_max:
            return int(new_max)

        if rate < new_min:
            return int(new_min)

        return int(rate)

    def _create_response(self):
        data = None
        LOGGER.debug('Url for request: %s', self.url)

        try:
            data = self.http_pool.urlopen('GET', self.url,
                                          preload_content=False,
                                          retries=self.max_download_retries)

        except urllib3.exceptions.SSLError:
            LOGGER.debug('SSL cert not verified')

        except urllib3.exceptions.MaxRetryError:
            LOGGER.debug('MaxRetryError')

        except Exception as e:
            LOGGER.debug(str(e), exc_info=True)

        if data is not None:
            LOGGER.debug('resource URL: %s', self.url)
        else:
            LOGGER.debug('could not create resource URL.')
        return data

    # Calling all progress hooks
    def _call_progress_hooks(self, data):

        # noinspection PyTypeChecker
        for ph in self.progress_hooks:

            try:
                ph(data)

            except Exception as err:
                LOGGER.debug('Exception in callback: %s', ph.__name__)
                LOGGER.debug(err, exc_info=True)

    def download_to_memory(self):

        data = self._create_response()

        if data is None:
            return None

        self.content_length = self._get_content_length(data)

        if self.content_length is None:
            LOGGER.debug('content-Length not in headers')
            LOGGER.debug('callbacks will not show time left '
                         'or percent downloaded.')

        received_data = 0

        start_download = time.time()
        block = data.read(1)
        received_data += len(block)
        self.file_binary_data = block
        percent = self._calc_progress_percent(0, self.content_length)
        while 1:

            start_block = time.time()

            block = data.read(self.block_size)

            end_block = time.time()

            if len(block) == 0:
                break

            self.block_size = self._best_block_size(end_block - start_block, len(block))
            LOGGER.debug('Block size: %s', self.block_size)
            self.file_binary_data += block

            received_data += len(block)

            percent = self._calc_progress_percent(received_data,
                                                  self.content_length)

            time_left = self._calc_eta(start_download, time.time(),
                                       self.content_length,
                                       received_data)

            status = {'total': self.content_length,
                      'downloaded': received_data,
                      'status': 'downloading',
                      'percent_complete': percent,
                      'time': time_left}

            self._call_progress_hooks(status)

        status = {'total': self.content_length,
                  'downloaded': received_data,
                  'status': 'finished',
                  'percent_complete': percent,
                  'time': '00:00'}

        self._call_progress_hooks(status)
        LOGGER.debug('Download Complete')

    def download(self):

        LOGGER.debug('downloading to memory')
        self.download_to_memory()

        check = self._check_hash()

        if check is True or check is None:
            LOGGER.debug('writing to file')
            self._write_to_file()
            return True

        else:
            del self.file_binary_data
            if os.path.exists(self.filename):
                try:
                    os.remove(self.filename)
                except OSError:
                    pass
            return False
