# coding=utf-8

from .custom_logging import make_logger, Logged
from .validator import not_a_bool, not_a_positive_int, not_a_str, not_an_int, valid_bool, valid_float, valid_str, \
    valid_dict, valid_existing_path, valid_int, valid_list, valid_negative_int, valid_positive_int, Validator
from .custom_path import Path, create_temp_file, create_temp_dir
from .downloader import Downloader
from .progress import Progress, ProgressAdapter
from .singleton import Singleton
from .updater import GHUpdater, Version, GithubRelease, AVUpdater, AVRelease
from .threadpool import ThreadPool
from .decorators import TypedProperty
from .pastebin import create_new_paste
from .monkey import nice_exit

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
