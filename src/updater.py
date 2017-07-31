# coding=utf-8

from src.__version__ import __version__
from src.utils.updater import Updater

updater = Updater(
    current_version=__version__,
    av_user='132nd-etcher',
    av_repo='test',  # FIXME
    local_executable='emft.exe',
    channel='alpha',
)
