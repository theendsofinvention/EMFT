# coding=utf-8
"""
Convenience module for storing/restoring per-user configuration values
"""
from utils.custom_logging import make_logger
from utils.singleton import Singleton

# noinspection PyProtectedMember
from src import global_
from src.meta import Meta
from .values import ConfigValues

logger = make_logger(__name__)


class Config(Meta, ConfigValues, metaclass=Singleton):
    def __init__(self, config_file_path=None):

        if config_file_path is None:
            config_file_path = global_.PATH_CONFIG_FILE

        Meta.__init__(self, path=config_file_path)
        ConfigValues.__init__(self)

    @property
    def meta_header(self):
        return 'EMFT_CONFIG'

    @property
    def meta_version(self):
        return 4

    def upgrade_from_v1(self):
        if self.update_channel in ['alpha', 'beta']:
            self.__setitem__('update_channel', 'dev', _write=False)
        return True

    def upgrade_from_v2(self):
        for key in [
            'saved_games_path',
            'single_miz_output_folder',
            'auto_source_folder',
            'auto_output_folder',
            'single_miz_last',
            'skins_active_dcs_installation',
            'roster_last_dir',
            'dcs_custom_install_path',
            'dcs_custom_variant_path'
        ]:
            try:
                del self.data[key]
            except KeyError:
                pass
        return True

    def upgrade_from_v3(self):
        try:
            self._data['roster_miz_last_dir'] = dict(self._data['roster_last_dir'])
            del self._data['roster_last_dir']
        except KeyError:
            pass
        return True

    def meta_version_upgrade(self, from_version):
        if from_version == self.meta_version:
            return True
        upgrade_func = getattr(self, 'upgrade_from_v{}'.format(from_version))
        if upgrade_func:
            logger.info('updating Config to meta version {}'.format(from_version))
            return upgrade_func()

    def __getitem__(self, key):
        """Mutes KeyError"""
        return self.get(key)

    def __setitem__(self, key, value, _write=True):
        """Immediately writes any change to file"""
        super(Config, self).__setitem__(key, value)
        if _write:
            self.write()

    def write(self):
        if global_.TESTING:
            return
        super(Config, self).write()


logger.info('config: initializing')
config = Config()
logger.info('config: initialized')
