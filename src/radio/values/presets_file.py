# coding=utf-8

# coding=utf-8


from collections import OrderedDict

from utils import Path, make_logger

from src.meta import MetaFile

from .radio_array import RadioArray
logger = make_logger(__name__)


class PresetsFile(MetaFile):
    def meta_version_upgrade(self, from_version):
        pass

    @property
    def meta_version(self):
        return 1

    @property
    def meta_header(self):
        return 'RADIO_PRESETS'

    def __init__(self, path, init_dict: OrderedDict = None):
        path = Path(path)
        MetaFile.__init__(self, path, init_dict)

    def write(self):
        logger.info('writing "{}"'.format(self.path))
        sorted_data = OrderedDict()
        for k in sorted(self._data.keys()):
            sorted_data[k] = self._data[k]
        self._data = sorted_data
        super(PresetsFile, self).write()
