# coding=utf-8
from .dcs_skin import DCSSkin
from src.ui.main_ui_interface import I

import os
import re

from utils import make_logger, Path

from src.cfg import Config
from ._winreg import winreg, A_REG
from .saved_games import saved_games_path

from src import global_
# from src.cfg.cfg import Config

logger = make_logger(__name__)


class InvalidSavedGamesPath(ValueError):
    pass


class InvalidInstallPath(ValueError):
    pass


class AutoexecCFG:
    RE_VFS = re.compile(r'table\.insert\(options\.graphics\.VFSTexturePaths, "(?P<path>.*)"\)')

    def __init__(self, path):
        self._path = Path(path)
        self._vfs = set()
        self.parse_vfs()

    @property
    def mounted_vfs_paths(self) -> set:
        return self._vfs

    def parse_vfs(self):
        logger.debug('reading "{}"'.format(self._path.abspath()))
        with open(self._path.abspath()) as f:
            lines = f.readlines()
        if lines:
            for line in lines:
                m = self.RE_VFS.match(line)
                if m:
                    self._vfs.add(m.group('path'))
        logger.debug('found {} VFS path(s)'.format(len(self._vfs)))

    @property
    def path(self) -> Path:
        return self._path


class DCSInstall:
    RE_SKIN_NICE_NAME = re.compile(r'name = "(?P<skin_nice_name>.*)"')

    def __init__(self, install_path, saved_games_path_, version, label):
        self.__install = install_path if install_path else None
        self.__sg = saved_games_path_ if saved_games_path_ else None
        self.__version = str(version) if version else None
        self.__label = label
        self.__skins = {}
        self.__autoexec = None

    @staticmethod
    def __check_path(path: Path or None, exc):
        if path is not None:
            path = Path(path)
            if not all([path.exists(), path.isdir()]):
                raise exc(path)

    @property
    def label(self):
        return self.__label

    @property
    def install_path(self):
        self.__check_path(self.__install, InvalidInstallPath)
        return str(Path(self.__install).abspath()) if self.__install is not None else None

    @property
    def saved_games(self):
        self.__check_path(self.__sg, InvalidSavedGamesPath)
        return str(Path(self.__sg).abspath()) if self.__sg is not None else None

    @property
    def version(self):
        return self.__version

    @property
    def autoexec(self):
        return self.__autoexec

    @property
    def skins(self):
        return self.__skins

    def discover_skins(self):

        self.__skins = {}

        def scan_dir(p: Path):
            if not p.exists():
                logger.debug('skipping absent folder: {}'.format(p.abspath()))
                return
            logger.debug('scanning for skins in: {}'.format(p.abspath()))
            for ac_folder in os.scandir(p.abspath()):
                # logger.debug('scanning for skins in: {}'.format(ac_folder.path))
                ac_name = ac_folder.name
                if ac_folder.is_dir():
                    for skin_folder in os.scandir(ac_folder.path):
                        # logger.debug('scanning for skins in: {}'.format(skin_folder.path))
                        skin_name = skin_folder.name
                        skin_nice_name = None

                        try:
                            with open(Path(skin_folder.path).join('description.lua')) as f:
                                lines = f.readlines()
                                for line in lines:
                                    m = self.RE_SKIN_NICE_NAME.match(line)
                                    if m:
                                        skin_nice_name = m.group('skin_nice_name')
                        except FileNotFoundError:
                            pass

                        self.__skins['{}_{}'.format(ac_name, skin_name)] = DCSSkin(
                            skin_name, ac_name, str(skin_folder.path), skin_nice_name
                        )

        scan_dir(Path(self.install_path).joinpath('bazar', 'liveries'))
        scan_dir(Path(self.saved_games).joinpath('liveries'))

        logger.debug('found {} skins'.format(len(self.__skins)))

    @property
    def autoexec_cfg(self) -> AutoexecCFG:
        return self.__autoexec

    def discover_autoexec(self):
        autoexec_cfg_path = Path(self.__sg).joinpath('config', 'autoexec.cfg')
        if autoexec_cfg_path.exists():
            logger.debug('reading {}'.format(autoexec_cfg_path.abspath()))
            self.__autoexec = AutoexecCFG(autoexec_cfg_path)
        else:
            logger.warning('file does not exist: {}'.format(autoexec_cfg_path.abspath()))


class DCSInstalls:
    def __init__(self):
        self._database = {}
        self._installs = {}
        self.installs_props = {
            'stable': {
                'reg_key': global_.DCS['reg_key']['stable'],
                'sg_default': 'DCS',
                'install': None,
                'sg': None,
                'version': None,
                'autoexec_cfg': None,
            },
            'beta': {
                'reg_key': global_.DCS['reg_key']['beta'],
                'sg_default': 'DCS.openbeta',
                'install': None,
                'sg': None,
                'version': None,
                'autoexec_cfg': None,
            },
            'alpha': {
                'reg_key': global_.DCS['reg_key']['alpha'],
                'sg_default': 'DCS.openalpha',
                'install': None,
                'sg': None,
                'version': None,
                'autoexec_cfg': None,
            },
            'custom': {
                'reg_key': None,
                'sg_default': None,
                'install': None,
                'sg': None,
                'version': None,
                'autoexec_cfg': None,
            },
        }

    def __discover_install_path(self, k) -> Path or None:
        try:
            logger.debug('{}: looking up in registry'.format(k))
            with winreg.OpenKey(A_REG,
                                r'Software\Eagle Dynamics\{}'.format(
                                    self.installs_props[k]['reg_key'])) as aKey:
                p = Path(winreg.QueryValueEx(aKey, 'Path')[0])
                logger.debug('{}: found path: {}'.format(k, p.abspath()))
                return p
        except FileNotFoundError:
            logger.debug('{}: no install path found'.format(k))
            return None

    def get_install_path(self, k) -> Path or None:
        if k == 'custom':
            return Config().dcs_custom_install_path
        install_path = self.__discover_install_path(k)
        if install_path is None:
            logger.debug('{}: no install path found'.format(k))
            return None
        install_path = Path(install_path)
        install_path.must_be_a_dir(InvalidInstallPath)
        return install_path

    def get_variant(self, k):
        install_path = Path(self.installs_props[k]['install'])
        variant_path = Path(install_path.joinpath('dcs_variant.txt'))
        logger.debug('{}: looking for variant: {}'.format(k, variant_path.abspath()))
        if variant_path.exists():
            logger.debug('{}: found variant: "{}"; reading'.format(k, variant_path.abspath()))
            return saved_games_path.abspath().joinpath('DCS.{}'.format(variant_path.text()))
        else:
            logger.debug('{}: no variant, falling back to default: {}'.format(k, self.installs_props[k]['sg_default']))
            return saved_games_path.abspath().joinpath(self.installs_props[k]['sg_default'])

    def discover_dcs_installations(self):
        logger.debug('looking for local DCS installations')

        for k in self.installs_props:

            logger.debug('{}: searching for paths'.format(k))

            if k == 'custom':
                install_path = Config().dcs_custom_install_path
                if isinstance(install_path, str):
                    install_path = Path(install_path)
            else:
                install_path = self.get_install_path(k)

            if install_path is None:
                logger.info('{}: no installation found, skipping'.format(k))
                continue

            exe = Path(install_path.joinpath('bin').joinpath('dcs.exe'))
            if not exe.exists():
                logger.info('{}: no executable found, skipping'.format(k))
                continue

            logger.debug('{}: install found: {}'.format(k, install_path.abspath()))

            self.installs_props[k]['install'] = str(install_path.abspath())
            if k =='custom':
                self.installs_props[k]['sg'] = Config().dcs_custom_variant_path
            else:
                self.installs_props[k]['sg'] = self.get_variant(k)

            logger.debug('{}: getting version info from executable: {}'.format(k, exe.abspath()))
            self.installs_props[k]['version'] = exe.get_win32_file_info().file_version

            logger.debug('{}: set "Saved Games" path to: {}'.format(k, self.installs_props[k]['sg']))

            install = DCSInstall(*self.__get_props(k))

            self._installs[k] = install

            install.discover_skins()
            install.discover_autoexec()

            I.config_tab_update_dcs_installs()
            I.tab_skins_update_dcs_installs_combo()

    def __get_props(self, channel):
        return self.installs_props[channel]['install'], \
               self.installs_props[channel]['sg'], self.installs_props[channel]['version'], channel

    @property
    def stable(self) -> DCSInstall:
        return self._installs.get('stable', None)

    @property
    def beta(self) -> DCSInstall:
        return self._installs.get('beta', None)

    @property
    def alpha(self) -> DCSInstall:
        return self._installs.get('alpha', None)

    @property
    def custom(self) -> DCSInstall:
        return self._installs.get('custom', None)

    @property
    def present_dcs_installations(self):
        for x in self:
            if x and x.install_path:
                yield x

    def __iter__(self) -> DCSInstall:
        yield self.stable
        yield self.beta
        yield self.alpha
        yield self.custom

    def __getitem__(self, item) -> DCSInstall:
        return getattr(self, item)

    def add_custom(self, install_dir: Path, variant_dir: Path):

        msg = 'custom: adding custom DCS installation; install_dir: "{}" Variant: "{}"'
        logger.info(msg.format(install_dir.abspath(), variant_dir.abspath()))

        exe = Path(install_dir.joinpath('bin').joinpath('dcs.exe'))
        logger.debug('custom: looking for dcs.exe: "{}"'.format(exe.abspath()))
        if not exe.exists():
            msg = '"dcs.exe" not found in:{{}}{}'.format(install_dir.abspath())
            logger.error(msg.format(''))
            I.error(msg.format('\n\n'))
            return

        logger.debug('custom: install found: {}'.format(install_dir.abspath()))

        self.installs_props['custom']['install'] = str(install_dir.abspath())
        self.installs_props['custom']['sg'] = str(variant_dir.abspath())

        logger.debug('custom: getting version info from executable: {}'.format(exe.abspath()))
        self.installs_props['custom']['version'] = exe.get_win32_file_info().file_version

        logger.debug('custom: set "Saved Games" path to: {}'.format(self.installs_props['custom']['sg']))

        install = DCSInstall(*self.__get_props('custom'))

        self._installs['custom'] = install

        install.discover_skins()
        install.discover_autoexec()

        Config().dcs_custom_install_path = self.installs_props['custom']['install']
        Config().dcs_custom_variant_path = self.installs_props['custom']['sg']

        I.config_tab_update_dcs_installs()
        I.tab_skins_update_dcs_installs_combo()

    def remove_custom(self):

        Config().dcs_custom_install_path = ''
        Config().dcs_custom_variant_path = ''

        del self._installs['custom']

        I.config_tab_update_dcs_installs()
        I.tab_skins_update_dcs_installs_combo()



dcs_installs = DCSInstalls()
