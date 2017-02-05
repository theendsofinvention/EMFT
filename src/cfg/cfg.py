# coding=utf-8
"""
Convenience module for storing/restoring per-user configuration values
"""
# noinspection PyProtectedMember
from src import _global
from src.meta.meta import Meta
from src.utils.custom_logging import make_logger
from src.utils.singleton import Singleton
from .values import ConfigValues

logger = make_logger(__name__)


class Config(Meta, ConfigValues, metaclass=Singleton):
    def __init__(self, config_file_path=None):
        if config_file_path is None:
            config_file_path = _global.PATH_CONFIG_FILE
        Meta.__init__(self, path=config_file_path)
        ConfigValues.__init__(self)

    @property
    def meta_header(self):
        return 'EMFT_CONFIG'

    def __getitem__(self, key):
        """Mutes KeyError"""
        return self.get(key, None)

    def __setitem__(self, key, value, _write=True):
        """Immediately writes any change to file"""
        super(Config, self).__setitem__(key, value)
        if _write:
            self.write()

    def write(self):
        if _global.TESTING:
            return
        super(Config, self).write()


logger.info('config: initializing')
config = Config()
logger.info('config: initialized')
