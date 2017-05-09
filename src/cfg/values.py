# coding=utf-8

import path
from utils.custom_logging import make_logger

from src.meta import MetaProperty

logger = make_logger(__name__)


class ConfigValues:
    @MetaProperty(None, str)
    def saved_games_path(self, value: str):
        p = path.Path(value)
        if not p.exists():
            raise FileNotFoundError('path does not exist: {}'.format(p.abspath()))
        elif not p.isdir():
            raise TypeError('path is not a directory: {}'.format(p.abspath()))
        return str(p.abspath())

    @MetaProperty(None, str)
    def single_miz_output_folder(self, value: str):
        p = path.Path(value)
        if not p.exists():
            return None
        elif not p.isdir():
            return None
        return str(p.abspath())

    @MetaProperty(None, str)
    def auto_source_folder(self, value: str):
        p = path.Path(value)
        if not p.exists():
            return None
        elif not p.isdir():
            return None
        return str(p.abspath())

    @MetaProperty(None, str)
    def auto_output_folder(self, value: str):
        p = path.Path(value)
        if not p.exists():
            return None
        elif not p.isdir():
            return None
        return str(p.abspath())

    @MetaProperty(None, str)
    def single_miz_last(self, value: str):
        p = path.Path(value)
        if not p.exists():
            return None
        elif not p.isfile():
            return None
        elif not p.ext == '.miz':
            return None
        return str(p.abspath())

    @MetaProperty(True, bool)
    def skip_options_file(self, value: bool):
        return value

    @MetaProperty(None, str)
    def av_token(self, value: str):
        return value

    @MetaProperty(False, bool)
    def auto_mode(self, value: bool):
        return value

    @MetaProperty(True, bool)
    def allow_mv_autoexec_changes(self, value: bool):
        return value

    @MetaProperty('INFO', str)
    def log_level(self, value: str):
        if value not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ValueError(value)
        return value

    # noinspection PyPep8Naming
    @MetaProperty('All', str)
    def selected_TRMT_branch(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaProperty(None, str)
    def skins_active_dcs_installation(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaProperty(None, str)
    def roster_last_dir(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaProperty('stable', str)
    def update_channel(self, value: str):
        if value not in ['stable', 'rc', 'dev', 'beta', 'alpha']:
            raise ValueError('unknown update channel: {}'.format(value))
        return value
