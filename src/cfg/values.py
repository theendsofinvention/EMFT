# coding=utf-8

import path
from utils.custom_logging import make_logger

from src.meta import MetaPropertyWithDefault, MetaGUIDPropertyWithDefault

logger = make_logger(__name__)


class ConfigValues:
    @MetaGUIDPropertyWithDefault(None, str)
    def saved_games_path(self, value: str):
        if value:
            p = path.Path(value)
            if not p.exists():
                raise FileNotFoundError('path does not exist: {}'.format(p.abspath()))
            elif not p.isdir():
                raise TypeError('path is not a directory: {}'.format(p.abspath()))
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def single_miz_output_folder(self, value: str):
        if value:
            p = path.Path(value)
            if not p.exists():
                return None
            elif not p.isdir():
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def auto_source_folder(self, value: str):
        if value:
            p = path.Path(value)
            if not p.exists():
                return None
            elif not p.isdir():
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def auto_output_folder(self, value: str):
        if value:
            p = path.Path(value)
            if not p.exists():
                return None
            elif not p.isdir():
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def single_miz_last(self, value: str):
        if value:
            p = path.Path(value)
            if not p.exists():
                return None
            elif not p.isfile():
                return None
            elif not p.ext == '.miz':
                return None
            return str(p.abspath())

    @MetaPropertyWithDefault(True, bool)
    def skip_options_file(self, value: bool):
        return value

    @MetaPropertyWithDefault(None, str)
    def av_token(self, value: str):
        return value

    @MetaPropertyWithDefault(False, bool)
    def auto_mode(self, value: bool):
        return value

    @MetaPropertyWithDefault(True, bool)
    def allow_mv_autoexec_changes(self, value: bool):
        return value

    @MetaPropertyWithDefault('INFO', str)
    def log_level(self, value: str):
        if value not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ValueError(value)
        return value

    # noinspection PyPep8Naming
    @MetaPropertyWithDefault('All', str)
    def selected_TRMT_branch(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def skins_active_dcs_installation(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def roster_roster_last_dir(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def roster_miz_last_dir(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaPropertyWithDefault('stable', str)
    def update_channel(self, value: str):
        if value not in ['stable', 'rc', 'dev', 'beta', 'alpha']:
            raise ValueError('unknown update channel: {}'.format(value))
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def dcs_custom_install_path(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def dcs_custom_variant_path(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def tab_radios_meta_path(self, value: str):
        return value

    # noinspection PyPep8Naming
    @MetaGUIDPropertyWithDefault(None, str)
    def tab_radios_meta_path_last_dir(self, value: str):
        return value
